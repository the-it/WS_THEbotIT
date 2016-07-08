__author__ = 'erik'

import sys
import os
import pywikibot
from pywikibot.data.api import LoginManager
import re
import traceback
import datetime
from datetime import timedelta

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + os.sep + os.pardir + os.sep + os.pardir + os.sep )

from tools.catscan import CatScan
from tools.bots import CanonicalBot, SaveExecution

class REStatus(CanonicalBot):
    def __init__(self, wiki):
        CanonicalBot.__init__(self, wiki)
        self.botname = 'REStatus'
        self.searcher = CatScan()

    def run(self):
        list_of_lemmas = self.petscan(['Teilkorrigiert RE', 'Korrigiert RE'])
        sum = 0
        for lemma in list_of_lemmas:
            sum += int(lemma['len'])
        print(sum)

    def petscan(self, categories):
        for category in categories:
            self.searcher.add_positive_category(category)
        self.searcher.set_logic_union()
        return self.searcher.run()

if __name__ == "__main__":
    with open('../password.pwd') as password:
        wiki = pywikibot.Site(code='de', fam='wikisource', user='THEbotIT')
        login = LoginManager(site=wiki, password=password.read())
        login.login()
    bot = REStatus(wiki)
    with SaveExecution(bot):
        bot.run()
