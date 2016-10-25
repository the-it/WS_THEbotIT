import re
import time
import operator
from datetime import datetime, timedelta
from tools.catscan import PetScan

from tools.bots import CanonicalBot

class ReScannerTask():
    def __init__(self, wiki, debug):
        self.reporter_page = None


class ReScanner(CanonicalBot):
    def __init__(self, wiki, debug):
        CanonicalBot.__init__(self, wiki, debug)
        self.botname = 'ReScanner'
        self.lemma_list = None
        self.new_data_model = datetime(year=2016, month=10, day=24, hour=23)
        self.timeout = timedelta(seconds=4)

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
        new_lemma_list = [x['title'] for x in raw_lemma_list if x['title'] not in list(self.data.keys())]
        # before processed lemmas ordered by last process time
        old_lemma_list = [x[0] for x in sorted(self.data.items(), key=operator.itemgetter(1))]
        return new_lemma_list + old_lemma_list

    def run(self):
        self.lemma_list = self.compile_lemma_list()
        for lemma in self.lemma_list:
            self.logger.info('Process {}'.format(lemma))
            self.data[lemma] = datetime.now().strftime('%Y%m%d%H%M%S')
            time.sleep(1)
            if self._watchdog():
                break
