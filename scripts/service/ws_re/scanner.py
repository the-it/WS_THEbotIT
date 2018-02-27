import re
from abc import abstractmethod
from datetime import datetime, timedelta
from logging import Logger
from operator import itemgetter

from pywikibot import Page, Site

from scripts.service.ws_re.data_types import RePage
from tools.bots import CanonicalBot
from tools.catscan import PetScan


class ReScannerTask(object):
    def __init__(self, wiki: Site, debug: bool, logger: Logger):
        self.reporter_page = None
        self.wiki = wiki
        self.debug = debug
        self.logger = logger
        self.hash = None
        self.re_page = None
        self.pre_process_hash = None
        self.text = None

    def __del__(self):
        self.finish_task()

    def pre_process_lemma(self, re_page: RePage):
        self.re_page = re_page
        self.pre_process_hash = hash(re_page)

    def post_process_lemma(self):
        return self.pre_process_hash != hash(self.re_page)

    @abstractmethod
    def task(self):
        pass

    def process_lemma(self, re_page: RePage):
        self.pre_process_lemma(re_page)
        self.task()
        return self.post_process_lemma()

    def load_task(self):
        self.logger.info('opening task {}'.format(self.get_name()))

    def finish_task(self):
        self.logger.info('closing task {}'.format(self.get_name()))

    def get_name(self):
        return re.search("(.{4})Task", str(self.__class__)).group(1)


class ENUUTask(ReScannerTask):
    def __init__(self, wiki: Site, debug: bool, logger: Logger):
        ReScannerTask.__init__(self, wiki, debug, logger)
        self.load_task()

    def task(self):
        self.text = re.sub(r'\n*\{\{REDaten.*?\n\}\}\s*', self.replace_re, self.text, flags=re.DOTALL)
        self.text = re.sub(r'\n*\{\{REAutor.*?\}\}\s*', self.replace_re, self.text, flags=re.DOTALL)
        self.text = re.sub(r'\n*\{\{REAbschnitt.*?\}\}\s*', self.replace_re, self.text, flags=re.DOTALL)
        self.text = self.text.rstrip()
        if self.text[0] == '\n':
            self.text = self.text[1:]

    @staticmethod
    def replace_re(hit: re):
        return '\n' + hit.group(0).strip(" \n\t") + '\n'


class ReScanner(CanonicalBot):
    bot_name = 'ReScanner'

    def __init__(self, wiki, debug):
        CanonicalBot.__init__(self, wiki, debug)
        self.lemma_list = None
        self.new_data_model = datetime(year=2016, month=11, day=8, hour=11)
        self.timeout = timedelta(seconds=60)  # bot should run only one minute ... don't do anything at the moment
        self.tasks = [ENUUTask]
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
        self.lemma_list = new_lemma_list + old_lemma_list  # first iterate new items then the old ones (oldest first)

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
                    self.logger.info('Änderungen durch Task {} durchgeführt'.format(task.get_name()))
                    page.save('RE Scanner hat folgende Aufgaben bearbeitet: {}'.format(', '.join(list_of_done_tasks)),
                              botflag=True)
            self.data[lemma] = datetime.now().strftime('%Y%m%d%H%M%S')
            if self._watchdog():
                break
        for task in self.tasks:
            del task
        return True


if __name__ == "__main__":
    WS_WIKI = Site(code='de', fam='wikisource', user='THEbotIT')
    with ReScanner(wiki=WS_WIKI, debug=True) as bot:
        bot.run()
