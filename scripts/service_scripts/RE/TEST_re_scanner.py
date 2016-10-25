import re
import time
import operator
from datetime import datetime, timedelta
from tools.catscan import PetScan
from pywikibot import Page

from tools.bots import CanonicalBot

class ReScannerTask():
    def __init__(self, wiki, debug, logger):
        self.reporter_page = None
        self.wiki = wiki
        self.debug = debug
        self.logger = logger
        self.task_name = 'basic_task'
        self.load_task()

    def __del__(self):
        self.finish_task()

    def process_lemma(self, page:Page):
        self.logger.info('process {} with task {}'.format(page, self.task_name))

    def load_task(self):
        self.logger.info('opening {}'.format(self.task_name))

    def finish_task(self):
        self.logger.info('closing {}'.format(self.task_name))

class ReScanner(CanonicalBot):
    def __init__(self, wiki, debug):
        CanonicalBot.__init__(self, wiki, debug)
        self.botname = 'ReScanner'
        self.lemma_list = None
        self.new_data_model = datetime(year=2016, month=10, day=24, hour=23)
        self.timeout = timedelta(seconds=4)
        self.tasks = [ReScannerTask]

    def __enter__(self):
        CanonicalBot.__enter__(self)
        if self.data_outdated():
            self.data = None
            self.logger.warning('The data is thrown away. It is out of date')
        if not self.data:
            self.data = {}

    def compile_lemma_list(self):
        self.logger.info('Compile the lemma list')
        searcher = PetScan()
        searcher.add_any_template('RE')
        searcher.add_any_template('REDaten')
        if self.debug:
            searcher.add_namespace(2)
        else:
            searcher.add_namespace(0)
            searcher.add_positive_category('Fertig RE')
            searcher.add_positive_category('Korrigiert RE')
            searcher.set_logic_union()
        self.logger.info(searcher)
        raw_lemma_list = searcher.run()
        # all items which wasn't process before
        new_lemma_list = [x['nstext'] + ':' + x['title'] for x in raw_lemma_list if x['title'] not in list(self.data.keys())]
        # before processed lemmas ordered by last process time
        old_lemma_list = [x[0] for x in sorted(self.data.items(), key=operator.itemgetter(1))]
        return new_lemma_list + old_lemma_list

    def run(self):
        active_tasks = []
        for task in self.tasks:
            active_tasks.append(task(self.wiki, self.debug, self.logger))
        self.lemma_list = self.compile_lemma_list()
        self.logger.info('Start processing the lemmas.')
        for lemma in self.lemma_list:
            page = Page(self.wiki, lemma)
            for task in active_tasks:
                task.process_lemma(page)
            self.data[lemma] = datetime.now().strftime('%Y%m%d%H%M%S')
            time.sleep(1)
            if self._watchdog():
                break

        for task in self.tasks:
            del task
