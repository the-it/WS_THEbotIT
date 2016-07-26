__author__ = 'erik'

import sys
import os
import pywikibot
from pywikibot.data.api import LoginManager
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + os.sep + os.pardir + os.sep + os.pardir + os.sep )

from tools.catscan import PetScan
from tools.bots import CanonicalBot, SaveExecution
from tools.little_helpers import load_password

class TouchIndex(CanonicalBot):
    def __init__(self, wiki):
        CanonicalBot.__init__(self, wiki)
        self.botname = 'PingIndex'
        self.searcher = PetScan()
        self.timeout = timedelta(hours=4)

    def run(self):
        indexes = self.petscan()
        sum = 0
        self.logger.info('There are {} indexes currently'.format(len(indexes)))
        for idx, index in enumerate(indexes):
            if self._watchdog():
                break
            touch_date = datetime.strptime(index['touched'], '%Y%m%d%H%M%S')
            now = datetime.now()
            diff = now - touch_date
            self.logger.debug('{}/{} {}'.format(idx, len(indexes), index['title']))
            if diff.days > 2:
                self.logger.debug('Touch index {}'.format(index['title']))
                touchpage = pywikibot.Page(self.wiki, 'Index:{}'.format(index['title']))
                touchpage.touch()
                sum += 1
        self.logger.info('Touched {} indexes.'.format(sum))

    def petscan(self):
        for cat in ['Fertig', 'Korrigiert', 'Teilkorrigiert', 'Unkorrigiert', 'Unvollständig']:
            self.searcher.add_positive_category(cat)
        self.searcher.set_logic_union()
        self.searcher.set_sort_criteria('date')
        self.searcher.add_namespace('Index')
        return self.searcher.run()

if __name__ == "__main__":
    with open('../password.pwd') as password_file:
        password = load_password(password_file)
        wiki = pywikibot.Site(code='de', fam='wikisource', user='THEbotIT')
        login = LoginManager(site=wiki, password=password)
        login.login()
    bot = TouchIndex(wiki)
    with SaveExecution(bot):
        bot.run()
