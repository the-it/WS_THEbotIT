import sys
import os
import pywikibot
import re
from pywikibot.data.api import LoginManager

from pywikibot.proofreadpage import ProofreadPage

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + os.sep + os.pardir + os.sep + os.pardir + os.sep )

from tools.catscan import PetScan
from tools.bots import CanonicalBot, SaveExecution
from tools.little_helpers import load_password

class MagazinesGL(CanonicalBot):
    def __init__(self, wiki):
        CanonicalBot.__init__(self, wiki)
        self.botname = 'MagazinesGL'
        self.searcher_pages = PetScan()
        self.searcher_indexes = PetScan()
        self.regex_page = re.compile('Die_Gartenlaube_\((\d{4})\)_([^\.]*?)\.jpg')

    def __enter__(self):
        CanonicalBot.__enter__(self)
        if not self.data:
            self.data = {'pages':{}, 'indexes':{}}

    def run(self):
        self.indexes = self.search_indexes()
        self.lemmas = self.search_pages()
        self.process_pages()

    def process_pages(self):
        for lemma in self.lemmas:
            hit = self.regex_page.search(lemma['title'])
            year = hit.group(1)
            page = hit.group(2)
            if not year in self.data['pages'].keys():
                self.data['pages'][year] = {}
            proofread_lemma = ProofreadPage(self.wiki, 'Seite:Die Gartenlaube (1898) 0000 a.jpg')
            print(proofread_lemma.status)
            self.data['pages'][year][page] = proofread_lemma.status

    def search_indexes(self):
        self.searcher_indexes.add_positive_category('Die Gartenlaube')
        self.searcher_indexes.add_positive_category('Index')
        self.searcher_indexes.set_regex_filter('.*Die Gartenlaube \(\d{4}\)')
        if self.last_run and self.last_run['succes'] and self.data:
            self.create_timestamp_for_search(self.searcher_indexes)
        return self.searcher_indexes.run()

    def search_pages(self):
        self.searcher_pages.add_positive_category('Die Gartenlaube')
        self.searcher_pages.add_namespace('Seite')
        self.searcher_pages.set_search_depth(1)
        if self.last_run and self.last_run['succes'] and self.data:
            self.create_timestamp_for_search(self.searcher_pages)
        elif __debug__:
        #elif False:
            self.create_timestamp_for_search(self.searcher_pages, 5)
        return self.searcher_pages.run()


if __name__ == "__main__":
    with open('../password.pwd') as password_file:
        password = load_password(password_file)
        wiki = pywikibot.Site(code= 'de', fam= 'wikisource', user='THEbotIT')
        login = LoginManager(site=wiki, password=password)
        login.login()

    bot = MagazinesGL(wiki)
    with SaveExecution(bot):
        bot.run()
