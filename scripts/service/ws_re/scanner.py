import re
from abc import abstractmethod
from datetime import datetime, timedelta
from operator import itemgetter

from pywikibot import Page, Site

from scripts.service.ws_re.data_types import RePage
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
        self.hash = None
        self.re_page = None
        self.load_task()
        self.result = {SUCCESS: False, CHANGED: False}
        self.processed_pages = []

    def __del__(self):
        self.finish_task()

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
        return re.search("([A-Z]{4})[A-Za-z]*?Task", str(self.__class__)).group(1)


class ReScanner(CanonicalBot):
    def __init__(self, wiki: Site = None, debug: bool = True, silence: bool = False):
        CanonicalBot.__init__(self, wiki, debug, silence)
        self.timeout = timedelta(seconds=60)
        self.tasks = []
        if self.debug:
            self.tasks = self.tasks + []

    def _prepare_searcher(self):
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

    def compile_lemma_list(self):
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

    def task(self):
        pass

    def old_task(self):
        active_tasks = []
        for task in self.tasks:
            active_tasks.append(task(self.wiki, self.debug, self.logger))
        lemma_list = self.compile_lemma_list()
        self.logger.info('Start processing the lemmas.')
        for lemma in lemma_list:
            list_of_done_tasks = []
            page = Page(self.wiki, lemma)
            self.logger.info('Process {}'.format(page))
            for task in active_tasks:
                if task.process_lemma(page):
                    list_of_done_tasks.append(task.get_name())
                    self.logger.info('Änderungen durch Task {} durchgeführt'
                                     .format(task.get_name()))
                    page.save('RE Scanner hat folgende Aufgaben bearbeitet: {}'
                              .format(', '.join(list_of_done_tasks)),
                              botflag=True)
            self.data[lemma] = datetime.now().strftime('%Y%m%d%H%M%S')
            if self._watchdog():
                break
        for task in self.tasks:
            del task
        return True


if __name__ == "__main__":
    WS_WIKI = Site(code='de', fam='wikisource', user='THEbotIT')
    with ReScanner(wiki=WS_WIKI, debug=False) as bot:
        bot.run()
