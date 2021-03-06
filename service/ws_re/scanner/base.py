import traceback
from contextlib import suppress
from datetime import timedelta, datetime
from operator import itemgetter
from typing import List, Optional, Dict, Callable

import pywikibot

from service.ws_re.scanner.tasks.author_or_redirect import REAUTask
from service.ws_re.scanner.tasks.base_task import ReScannerTask
from service.ws_re.scanner.tasks.death_re_links import DEALTask
from service.ws_re.scanner.tasks.death_wp_links import DEWPTask
from service.ws_re.scanner.tasks.error_handling import ERROTask
from service.ws_re.scanner.tasks.gemeinfrei_2021 import GF21Task
from service.ws_re.scanner.tasks.keine_schoepfungshoehe import KSCHTask
from service.ws_re.scanner.tasks.register_scanner import SCANTask
from service.ws_re.scanner.tasks.wikidata.task import DATATask
from service.ws_re.template import ReDatenException
from service.ws_re.template.re_page import RePage
from tools._typing import PetscanLemma
from tools.bots import BotException
from tools.bots.pi import CanonicalBot
from tools.petscan import PetScan, PetScanException


class ReScanner(CanonicalBot):
    def __init__(self, wiki: pywikibot.Site = None, debug: bool = True,
                 log_to_screen: bool = True, log_to_wiki: bool = True):
        CanonicalBot.__init__(self, wiki, debug, log_to_screen, log_to_wiki)
        self.timeout = timedelta(hours=8)
        self.tasks: List[Callable] = [KSCHTask, DEALTask, DEWPTask, REAUTask, GF21Task, DATATask, SCANTask]
        if self.debug:
            self.tasks = self.tasks + []
        self.statistic: Dict[str, int] = {}

    def __enter__(self):
        super().__enter__()
        if not self.data:
            self.logger.warning("Try to get the deprecated data back.")
            try:
                self.data.get_deprecated()
            except BotException:
                self.logger.warning("There isn't deprecated data to reload.")
        return self

    def compile_lemma_list(self) -> List[str]:
        self.logger.info("Compile the lemma list")
        self.logger.info("Searching for lemmas")
        raw_lemma_list = self._petscan_search()
        self.statistic["len_raw_lemma_list"] = len(raw_lemma_list)
        self.logger.info("Filter new_lemma_list")
        # all items which wasn't process before
        new_lemma_list = []
        for lemma in raw_lemma_list:
            try:
                self.data[lemma]
            except KeyError:
                new_lemma_list.append(lemma)
        self.statistic["len_new_lemma_list"] = len(new_lemma_list)
        self.logger.info("Sort old_lemma_list")
        # before processed lemmas ordered by last process time
        old_lemma_list = [x[0] for x in sorted(self.data.items(), key=itemgetter(1))]
        # first iterate new items then the old ones (oldest first)
        self.logger.info("Add the two lists")
        self.statistic["len_old_lemma_list"] = len(old_lemma_list)
        self.logger.info(f"raw: {self.statistic['len_raw_lemma_list']}, "
                         f"new: {self.statistic['len_new_lemma_list']}, "
                         f"old: {self.statistic['len_old_lemma_list']}")
        return new_lemma_list + old_lemma_list

    def _petscan_search(self) -> List[str]:
        searcher = self._prepare_searcher()
        self.logger.info(f"[{searcher} {searcher}]")
        raw_lemma_list: List[PetscanLemma] = []
        try:
            raw_lemma_list = searcher.run()
        except PetScanException:
            self.logger.error("Search timed out.")
        return [item["nstext"] + ":" + item["title"] for item in raw_lemma_list]

    def _prepare_searcher(self) -> PetScan:
        searcher = PetScan()
        searcher.add_yes_template("REDaten")

        if self.debug:
            searcher.add_namespace(2)
        else:
            searcher.add_namespace(0)
            searcher.add_positive_category("RE:Fertig")
            searcher.add_positive_category("RE:Korrigiert")
            searcher.add_positive_category("RE:Platzhalter")
            searcher.set_logic_union()
            searcher.set_sort_criteria("date")
            searcher.set_sortorder_decending()
            searcher.set_timeout(120)
        return searcher

    def _activate_tasks(self) -> List[ReScannerTask]:
        active_tasks = []
        for task in self.tasks:
            active_tasks.append(task(wiki=self.wiki, debug=self.debug, logger=self.logger))
        return active_tasks

    def _save_re_page(self, re_page: RePage, list_of_done_tasks: List[str]):
        if not self.debug:
            save_message = f"ReScanner hat folgende Aufgaben bearbeitet: {', '.join(list_of_done_tasks)}"
            self.logger.debug(save_message)
            try:
                re_page.save(save_message)
            except ReDatenException:
                self.logger.error("RePage can't be saved.")

    def _add_lemma_to_data(self, lemma: str):
        self.data[lemma] = datetime.now().strftime("%Y%m%d%H%M%S")

    def _process_task(self, task: ReScannerTask, re_page: RePage, lemma: str) -> Optional[str]:
        task_name = None
        with task:
            result = task.run(re_page)
            if result["success"]:
                if result["changed"]:
                    task_name = task.name
            else:
                if result["changed"]:
                    error_message = f"Error in {task.name}/[[{lemma}]], but altered the page ... critical"
                    self.logger.critical(error_message)
                    raise RuntimeError(error_message)
                self.logger.error(f"Error in {task.name}/[[{lemma}]], no data where altered.")
        return task_name

    def get_oldest_datetime(self) -> datetime:
        datetime_str = min(self.data.values())
        return datetime.strptime(datetime_str, "%Y%m%d%H%M%S")

    def task(self) -> bool:
        active_tasks = self._activate_tasks()
        error_task = ERROTask(wiki=self.wiki, debug=self.debug, logger=self.logger)
        lemma_list = self.compile_lemma_list()
        self.logger.info("Start processing the lemmas.")
        processed_lemmas = 0
        for idx, lemma in enumerate(lemma_list):
            self.logger.debug(f"Process [https://de.wikisource.org/wiki/{lemma} {lemma}]")
            list_of_done_tasks = []
            try:
                re_page = RePage(pywikibot.Page(self.wiki, lemma))
            except ReDatenException:
                error = traceback.format_exc().splitlines()[-1]
                self.logger.error(f"The initiation of [[{lemma}]] went wrong: {error}")
                error_task.append_error(lemma, error)
                # remove Key from database if it was saved before
                with suppress(KeyError):
                    del self.data[lemma]
                continue
            except pywikibot.exceptions.TimeoutError:
                self.logger.error(f"Timeout at lemma ({lemma}) creation")
                continue
            if re_page.has_changed():
                list_of_done_tasks.append("BASE")
            for task in active_tasks:
                processed_task = self._process_task(task, re_page, lemma)
                if processed_task:
                    list_of_done_tasks.append(processed_task)
            if list_of_done_tasks and re_page.is_writable:
                processed_lemmas += 1
                if not self.debug:
                    self._save_re_page(re_page, list_of_done_tasks)
            self._add_lemma_to_data(lemma)
            if self._watchdog():
                self.logger.info(f"{idx} Lemmas processed, {processed_lemmas} changed.")
                self.logger.info(f"Oldest processed item: {datetime.now() - self.get_oldest_datetime()}")
                break
        for task in active_tasks:
            task.finish_task()
        error_task.finish_task()
        return True


if __name__ == "__main__":  # pragma: no cover
    WS_WIKI = pywikibot.Site(code="de", fam="wikisource", user="THEbotIT")
    with ReScanner(wiki=WS_WIKI, debug=False) as bot:
        bot.run()
