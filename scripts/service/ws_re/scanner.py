import re
from abc import abstractmethod
from datetime import timedelta
from operator import itemgetter
from typing import List

from pywikibot import Page, Site

from scripts.service.ws_re.data_types import RePage, ReDatenException
from tools.bots import CanonicalBot, WikiLogger
from tools.catscan import PetScan

SUCCESS = "success"
CHANGED = "changed"


class ReScannerTask(object):
    def __init__(self, wiki: Site, logger: WikiLogger, debug: bool = True):
        self.reporter_page = None
        self.wiki = wiki
        self.debug = debug
        self.logger = logger
        self.re_page = None  # type: RePage
        self.load_task()
        self.result = {SUCCESS: False, CHANGED: False}
        self.processed_pages = []
        self.timeout = timedelta(minutes=1)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    def task(self):
        pass

    def run(self, re_page: RePage):
        self.re_page = re_page
        preprocessed_hash = hash(self.re_page)
        try:
            self.task()
        except Exception as exception:  # pylint: disable=broad-except
            self.logger.exception("Logging a caught exception", exception)
        else:
            self.result[SUCCESS] = True
            self.processed_pages.append(re_page.lemma)
        if preprocessed_hash != hash(self.re_page):
            self.result[CHANGED] = True
        return self.result

    def load_task(self):
        self.logger.info('opening task {}'.format(self.get_name()))

    def finish_task(self):
        self.logger.info('closing task {}'.format(self.get_name()))

    def get_name(self):
        return re.search("([A-Z0-9]{4})[A-Za-z]*?Task", str(self.__class__)).group(1)


class ReScanner(CanonicalBot):
    def __init__(self, wiki: Site = None, debug: bool = True,
                 log_to_screen: bool = True, log_to_wiki: bool = True):
        CanonicalBot.__init__(self, wiki, debug, log_to_screen, log_to_wiki)
        self.timeout = timedelta(seconds=60)
        self.tasks = []  # type: List[type(ReScannerTask)]
        if self.debug:
            self.tasks = self.tasks + []

    def _prepare_searcher(self) -> PetScan:
        searcher = PetScan()
        searcher.add_any_template('REDaten')

        if self.debug:
            searcher.add_namespace(2)
        else:
            searcher.add_namespace(0)
            searcher.add_positive_category('Fertig RE')
            searcher.add_positive_category('Korrigiert RE')
            searcher.add_positive_category('RE:Platzhalter')
            searcher.set_logic_union()
            searcher.set_sort_criteria("date")
            searcher.set_sortorder_decending()
        return searcher

    def compile_lemma_list(self) -> List[str]:
        self.logger.info('Compile the lemma list')
        searcher = self._prepare_searcher()
        self.logger.info('[{url} {url}]'.format(url=searcher))
        raw_lemma_list = searcher.run()
        # all items which wasn't process before
        new_lemma_list = [x['nstext'] + ':' + x['title'] for x in raw_lemma_list if
                          x['nstext'] + ':' + x['title'] not in list(self.data.keys())]
        # before processed lemmas ordered by last process time
        old_lemma_list = [x[0] for x in sorted(self.data.items(), key=itemgetter(1))]
        # first iterate new items then the old ones (oldest first)
        return new_lemma_list + old_lemma_list

    def _activate_tasks(self) -> List[ReScannerTask]:
        active_tasks = []
        for task in self.tasks:
            active_tasks.append(task(wiki=self.wiki, debug=self.debug, logger=self.logger))
        return active_tasks

    def _save_re_page(self, re_page: RePage, list_of_done_tasks: list):
        if not self.debug:
            save_message = 'ReScanner processed this task: {}' \
                .format(', '.join(list_of_done_tasks))
            self.logger.info(save_message)
            try:
                re_page.save(save_message)
            except ReDatenException:
                self.logger.error("RePage can't be saved.")

    def task(self) -> bool:
        active_tasks = self._activate_tasks()
        lemma_list = self.compile_lemma_list()
        self.logger.info('Start processing the lemmas.')
        for lemma in lemma_list:
            self.logger.info('Process [https://de.wikisource.org/wiki/{lemma} {lemma}]'
                             .format(lemma=lemma))
            list_of_done_tasks = []
            try:
                re_page = RePage(Page(self.wiki, lemma))
            except ReDatenException as initial_exception:
                self.logger.exception("The initiation of {} went wrong".format(lemma),
                                      initial_exception)
                continue
            if re_page.has_changed():
                list_of_done_tasks.append("BASE")
            for task in active_tasks:
                with task:
                    result = task.run(re_page)
                    if result["success"]:
                        if result["changed"]:
                            list_of_done_tasks.append(task.get_name())
                    else:
                        if result["changed"]:
                            error_message = "Error in {}/{}, but altered the page ... critical"\
                                .format(task.get_name(), lemma)
                            self.logger.critical(error_message)
                            raise RuntimeError(error_message)
                        else:
                            self.logger.error("Error in {}/{}, no data where altered."
                                              .format(task.get_name(), lemma))
            if list_of_done_tasks:
                self._save_re_page(re_page, list_of_done_tasks)
            if self._watchdog():
                break
        for task in active_tasks:
            task.finish_task()
        return True


if __name__ == "__main__":  # pragma: no cover
    WS_WIKI = Site(code='de', fam='wikisource', user='THEbotIT')
    with ReScanner(wiki=WS_WIKI, debug=False) as bot:
        bot.run()
