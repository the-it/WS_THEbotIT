import re
import time
from datetime import datetime, timedelta
from tools.catscan import PetScan

from tools.bots import CanonicalBot

class ReScanner(CanonicalBot):
    def __init__(self, wiki, debug):
        CanonicalBot.__init__(self, wiki, debug)
        self.botname = 'ReScanner'
        self.lemma_list = self.compile_lemma_list()
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
        searcher = PetScan()
        searcher.add_any_template('RE')
        searcher.add_any_template('REDaten')
        if self.debug:
            searcher.add_namespace(2)
        else:
            searcher.add_namespace(0)
        return searcher.run()

    def run(self):
        for lemma in self.lemma_list:
            if self._watchdog():
                break
            self.logger.info('{}, {}'.format(lemma['title'], lemma['touched']))
            print(lemma)
            time.sleep(1)
