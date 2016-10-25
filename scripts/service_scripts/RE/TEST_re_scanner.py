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
        self.text = ''
        self.task_name = 'basic_task'
        self.changed = False
        self.load_task()

    def __del__(self):
        self.finish_task()

    def preprocess_lemma(self, page:Page):
        self.logger.info('process {} with task {}'.format(page, self.task_name))
        self.text = page.text
        self.pretext = page.text
        self.changed = False

    def postprocess_lemma(self, page:Page):
        self.logger.info('processing {} with task {} finished'.format(page, self.task_name))
        page.text = self.text

    def load_task(self):
        self.logger.info('opening {}'.format(self.task_name))

    def finish_task(self):
        self.logger.info('closing {}'.format(self.task_name))

    def text_changed(self):
        return self.text != self.pretext


class ENÜU_Task(ReScannerTask):
    def __init__(self, wiki, debug, logger):
        ReScannerTask.__init__(self, wiki, debug, logger)
        self.task_name = 'ENÜU'
        self.load_task()

    def process_lemma(self, page:Page):
        self.preprocess_lemma(page)
        self.text = re.sub(r'\{\{REDaten.*?\n\}\}\n*', lambda x: self.replace_re(x), self.text, re.DOTALL)
        self.text = re.sub(r'\n*\{\{RENachtrag.*?\n\}\}\n*', lambda x: self.replace_re(x), self.text, re.DOTALL)
        self.text = re.sub(r'\n*\{\{REAutor.*?\n\}\}\n*', lambda x: self.replace_re_autor(x), self.text, re.DOTALL)
        self.postprocess_lemma(page)

    def replace_re(self, hit:str):
        return hit.strip() + '\n'

    def replace_re_autor(self, hit:str):
        return '\n' + hit.strip() + '\n'


class ReScanner(CanonicalBot):
    def __init__(self, wiki, debug):
        CanonicalBot.__init__(self, wiki, debug)
        self.botname = 'ReScanner'
        self.lemma_list = None
        self.new_data_model = datetime(year=2016, month=10, day=24, hour=23)
        self.timeout = timedelta(seconds=60)
        self.tasks = [ENÜU_Task]


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
        new_lemma_list = [x['nstext'] + ':' + x['title'] for x in raw_lemma_list if x['nstext'] + ':' + x['title'] not in list(self.data.keys())]
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
            changed = False
            page = Page(self.wiki, lemma)
            for task in active_tasks:
                task.process_lemma(page)
                changed = task.text_changed()
            self.data[lemma] = datetime.now().strftime('%Y%m%d%H%M%S')
            if changed:
                page.save('still testing')
            time.sleep(1)
            if self._watchdog():
                break
        for task in self.tasks:
            del task
