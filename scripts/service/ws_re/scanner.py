from datetime import timedelta, datetime
from operator import itemgetter
import traceback
from typing import List

from pywikibot import Page, Site

from scripts.service.ws_re.data_types import RePage, ReDatenException
from scripts.service.ws_re.scanner_tasks import ReScannerTask, ERROTask, KSCHTask
from tools.bots import CanonicalBot, BotException
from tools.catscan import PetScan


class ReScanner(CanonicalBot):
    def __init__(self, wiki: Site = None, debug: bool = True,
                 log_to_screen: bool = True, log_to_wiki: bool = True):
        CanonicalBot.__init__(self, wiki, debug, log_to_screen, log_to_wiki)
        self.timeout = timedelta(minutes=30)
        self.tasks = [KSCHTask]  # type: List[type[ReScannerTask]]
        if self.debug:
            self.tasks = self.tasks + []
        self.statistic = {}

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
        searcher.add_any_template('REDaten')

        if self.debug:
            searcher.add_namespace(2)
        else:
            searcher.add_namespace(0)
            searcher.add_positive_category('RE:Fertig')
            searcher.add_positive_category('RE:Korrigiert')
            searcher.add_positive_category('RE:Platzhalter')
            searcher.add_negative_category("Wikisource:Gemeinfreiheit|2")
            searcher.set_logic_union()
            searcher.set_sort_criteria("date")
            searcher.set_sortorder_decending()
            searcher.set_timeout(60)
        return searcher

    def compile_lemma_list(self) -> List[str]:
        self.logger.info('Compile the lemma list')
        self.logger.info('Searching for lemmas')
        searcher = self._prepare_searcher()
        self.logger.info('[{url} {url}]'.format(url=searcher))
        raw_lemma_list = searcher.run()
        self.statistic["len_raw_lemma_list"] = len(raw_lemma_list)
        self.logger.info("Filter new_lemma_list")
        # all items which wasn't process before
        new_lemma_list = []
        for item in raw_lemma_list:
            lemma = item['nstext'] + ':' + item['title']
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
        self.logger.info("raw: {}, new: {}, old: {}".format(self.statistic["len_raw_lemma_list"],
                                                            self.statistic["len_new_lemma_list"],
                                                            self.statistic["len_old_lemma_list"]))
        return new_lemma_list + old_lemma_list

    def _activate_tasks(self) -> List[ReScannerTask]:
        active_tasks = []
        for task in self.tasks:
            active_tasks.append(task(wiki=self.wiki, debug=self.debug, logger=self.logger))
        return active_tasks

    def _save_re_page(self, re_page: RePage, list_of_done_tasks: list):
        if not self.debug:
            save_message = 'ReScanner hat folgende Aufgaben bearbeitet: {}' \
                .format(', '.join(list_of_done_tasks))
            self.logger.debug(save_message)
            try:
                re_page.save(save_message)
            except ReDatenException:
                self.logger.error("RePage can't be saved.")

    def _add_lemma_to_data(self, lemma):
        self.data[lemma] = datetime.now().strftime("%Y%m%d%H%M%S")

    def _process_task(self, task: ReScannerTask, re_page: RePage, lemma: str) -> str:
        task_name = None
        with task:
            result = task.run(re_page)
            if result["success"]:
                if result["changed"]:
                    task_name = task.get_name()
            else:
                if result["changed"]:
                    error_message = "Error in {}/{}, but altered the page ... critical" \
                        .format(task.get_name(), lemma)
                    self.logger.critical(error_message)
                    raise RuntimeError(error_message)
                else:
                    self.logger.error("Error in {}/{}, no data where altered."
                                      .format(task.get_name(), lemma))
        return task_name

    def get_oldest_datetime(self):
        datetime_str = min(self.data.values())
        return datetime.strptime(datetime_str, "%Y%m%d%H%M%S")

    def task(self) -> bool:
        active_tasks = self._activate_tasks()
        error_task = ERROTask(wiki=self.wiki, debug=self.debug, logger=self.logger)
        lemma_list = self.compile_lemma_list()
        self.logger.info('Start processing the lemmas.')
        processed_lemmas = 0
        for idx, lemma in enumerate(lemma_list):
            self.logger.debug('Process [https://de.wikisource.org/wiki/{lemma} {lemma}]'
                              .format(lemma=lemma))
            list_of_done_tasks = []
            try:
                re_page = RePage(Page(self.wiki, lemma))
            except ReDatenException:
                error = traceback.format_exc().splitlines()[-1]
                self.logger.error("The initiation of {} went wrong: {}".format(lemma, error))
                error_task.task(lemma, error)
                self._add_lemma_to_data(lemma)
                continue
            if re_page.has_changed():
                list_of_done_tasks.append("BASE")
            for task in active_tasks:
                processed_task = self._process_task(task, re_page, lemma)
                if processed_task:
                    list_of_done_tasks.append(processed_task)
            if list_of_done_tasks:
                processed_lemmas += 1
                if not self.debug:
                    self._save_re_page(re_page, list_of_done_tasks)
            self._add_lemma_to_data(lemma)
            if self._watchdog():
                self.logger.info("{} Lemmas processed, {} changed.".format(idx, processed_lemmas))
                self.logger.info("Oldest processed item: {}"
                                 .format(str(datetime.now() - self.get_oldest_datetime())))
                break
        for task in active_tasks:
            task.finish_task()
        error_task.finish_task()
        return True


if __name__ == "__main__":  # pragma: no cover
    WS_WIKI = Site(code='de', fam='wikisource', user='THEbotIT')
    with ReScanner(wiki=WS_WIKI, debug=True) as bot:
        bot.run()
