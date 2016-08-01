__author__ = 'erik'

import sys
import os
import re
import traceback
import datetime
from datetime import timedelta

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + os.sep + os.pardir + os.sep + os.pardir + os.sep )

from pywikibot import Page, Site
from pywikibot.data.api import LoginManager
from tools.catscan import PetScan
from tools.bots import CanonicalBot, SaveExecution
from tools.little_helpers import load_password

class REStatus(CanonicalBot):
    def __init__(self, wiki, debug):
        CanonicalBot.__init__(self, wiki, debug)
        self.botname = 'REStatus'

    def run(self):
        fertig = self.get_sum_of_cat(['Fertig RE'])
        korrigiert = self.get_sum_of_cat(['Teilkorrigiert RE', 'Korrigiert RE'])
        unkorrigiert = self.get_sum_of_cat(['Unkorrigiert RE'])
        page = Page(self.wiki, 'Benutzer:THEbotIT/' + self.botname)
        temp_text = page.text
        composed_text = ''.join(['|-\n', '|', self.timestamp_start.strftime('%Y%m%d-%H%M'),
                         '||', str(unkorrigiert[1]), '||', str(unkorrigiert[0]),
                         '||', str(korrigiert[1]), '||', str(korrigiert[0]),
                         '||', str(fertig[1]), '||', str(fertig[0]), '\n<!--new line-->'])
        temp_text = re.sub('<!--new line-->', composed_text, temp_text)
        page.text = temp_text
        page.save('new dataset', botflag=True)

    def get_sum_of_cat(self, cats):
        list_of_lemmas = self.petscan(cats)
        byte_sum = 0
        for lemma in list_of_lemmas:
            byte_sum += int(lemma['len'])
        return byte_sum, len(list_of_lemmas)

    def petscan(self, categories):
        self.searcher = PetScan()
        for category in categories:
            self.searcher.add_positive_category(category)
        self.searcher.set_logic_union()
        self.logger.debug(self.searcher)
        return self.searcher.run()

if __name__ == "__main__":
    with open('../password.pwd') as password_file:
        password = load_password(password_file)
        wiki = Site(code='de', fam='wikisource', user='THEbotIT')
        login = LoginManager(site=wiki, password=password)
        login.login()
    bot = REStatus(wiki=wiki, debug=True)
    with SaveExecution(bot):
        bot.run()
