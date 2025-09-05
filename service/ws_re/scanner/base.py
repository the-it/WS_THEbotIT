import traceback
from contextlib import suppress
from datetime import timedelta, datetime
from typing import List, Optional, Dict, Callable

import pywikibot

from service.ws_re.scanner.tasks.add_short_description import KURZTask
from service.ws_re.scanner.tasks.author_or_redirect import REAUTask
from service.ws_re.scanner.tasks.base_task import ReScannerTask
from service.ws_re.scanner.tasks.categorize_redirects import CARETask
from service.ws_re.scanner.tasks.check_redirect_links import CHRETask
from service.ws_re.scanner.tasks.correct_pd_dates import COPDTask
from service.ws_re.scanner.tasks.death_re_links import DEALTask
from service.ws_re.scanner.tasks.death_wp_links import DEWPTask
from service.ws_re.scanner.tasks.error_handling import ERROTask
from service.ws_re.scanner.tasks.register_scanner import SCANTask
from service.ws_re.scanner.tasks.set_platzhalter import SEPLTask
from service.ws_re.scanner.tasks.wikidata.task import DATATask
from service.ws_re.scanner.tasks.wrong_article_order import WAORTask
from service.ws_re.template import ReDatenException
from service.ws_re.template.re_page import RePage
from tools.bots import BotException
from tools.bots.cloud_bot import CloudBot
from tools.petscan import PetScan, get_processed_time


class ReScanner(CloudBot):
    def __init__(self, wiki: pywikibot.Site = None, debug: bool = True,
                 log_to_screen: bool = True, log_to_wiki: bool = True):
        CloudBot.__init__(self, wiki, debug, log_to_screen, log_to_wiki)
        self.timeout = timedelta(hours=8)
        # This tasks are handled in that order for every scanned RePage, the order is not hard important,
        # but it makes sense to execute tasks that alter the lemma, before the metadata is written to
        # Wikidata and the Registers.
        self.tasks: List[Callable] = [
            KURZTask,  # add short description
            SEPLTask,  # if there is no Korrekturstand set, set it to "Platzhalter"
            DEALTask,  # check for dead links RE internal
            DEWPTask,  # check for dead links to Wikipedia
            REAUTask,  # check for integrity article must have an author, or it is a soft redirect
            COPDTask,  # removes properties after article is in common domain and corrects the birth and death date
            CARETask,  # put hard redirects to lemma in a category
            CHRETask,  # check if backlinks go over redirect pages
            DATATask,  # write out to Wikidata
            SCANTask,  # write out to Registers
            WAORTask,  # look for Lemma where the content article isn't the first on the page
        ]
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

    def _prepare_searcher(self) -> PetScan:
        searcher = PetScan()
        searcher.add_yes_template("REDaten")

        if self.debug:
            searcher.add_namespace(2)
        else:
            searcher.add_namespace(0)
            searcher.add_positive_category("RE:Fertig")
            searcher.add_positive_category("RE:Korrigiert")
            searcher.add_positive_category("RE:Unkorrigiert")
            searcher.add_positive_category("RE:Platzhalter")
            searcher.set_logic_union()
            searcher.set_sort_criteria("date")
            searcher.set_sortorder_decending()
            searcher.set_timeout(120)
        return searcher

    @property
    def lemma_list(self) -> list[str]:
        searcher = self._prepare_searcher()
        result, _ = searcher.get_combined_lemma_list(self.data, timeframe=36)
        return result

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
                self.logger.error(f"Error in {task.name}/[[{lemma}]], no data was altered.")
        return task_name

    def get_oldest_datetime(self) -> datetime:
        datetime_str = min(self.data.values())
        return datetime.strptime(datetime_str, "%Y%m%d%H%M%S")

    def task(self) -> bool:
        active_tasks = self._activate_tasks()
        error_task = ERROTask(wiki=self.wiki, debug=self.debug, logger=self.logger)
        self.logger.info("Start processing the lemmas.")
        processed_lemmas = 0
        for idx, lemma in enumerate(self.lemma_list):
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
            self.data[lemma] = get_processed_time()
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
