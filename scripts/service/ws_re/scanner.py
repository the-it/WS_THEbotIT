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
            if preprocessed_hash != hash(self.re_page):
                self.result[CHANGED] = True
        except Exception as exception:  # pylint: disable=broad-except
            self.logger.exception("Logging a caught exception", exception)
        else:
            self.result[SUCCESS] = True
        return self.result

    def load_task(self):
        self.logger.info('opening task {}'.format(self.get_name()))

    def finish_task(self):
        self.logger.info('closing task {}'.format(self.get_name()))

    def get_name(self):
        return re.search("([A-Z]{4})[A-Za-z]*?Task", str(self.__class__)).group(1)


class ReScanner(CanonicalBot):
    def __init__(self, wiki, debug):
        CanonicalBot.__init__(self, wiki, debug)
        self.lemma_list = None
        self.new_data_model = datetime(year=2016, month=11, day=8, hour=11)
        # bot should run only one minute ... don't do anything at the moment
        self.timeout = timedelta(seconds=60)
        self.tasks = []
        if self.debug:
            self.tasks = self.tasks + []

    def __enter__(self):
        CanonicalBot.__enter__(self)
        if not self.data:
            self.data.assign_dict(dict())
        return self

    def compile_lemma_list(self):
        self.logger.info('Compile the lemma list')
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
        self.logger.info('[{url} {url}]'.format(url=searcher))
        raw_lemma_list = searcher.run()
        # all items which wasn't process before
        new_lemma_list = [x['nstext'] + ':' + x['title'] for x in raw_lemma_list if
                          x['nstext'] + ':' + x['title'] not in list(self.data.keys())]
        # before processed lemmas ordered by last process time
        old_lemma_list = [x[0] for x in sorted(self.data.items(), key=itemgetter(1))]
        # first iterate new items then the old ones (oldest first)
        self.lemma_list = new_lemma_list + old_lemma_list

    def task(self):
        active_tasks = []
        for task in self.tasks:
            active_tasks.append(task(self.wiki, self.debug, self.logger))
        self.compile_lemma_list()
        self.logger.info('Start processing the lemmas.')
        for lemma in self.lemma_list:
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
