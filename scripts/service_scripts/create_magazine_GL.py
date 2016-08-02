import sys
import os
import re

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + os.sep + os.pardir + os.sep + os.pardir + os.sep )

from pywikibot import Site, Page
from pywikibot.data.api import LoginManager
from pywikibot.proofreadpage import ProofreadPage, IndexPage
from tools.catscan import PetScan
from tools.bots import CanonicalBot, SaveExecution
from tools.little_helpers import load_password

class MagazinesGL(CanonicalBot):
    def __init__(self, wiki, debug):
        CanonicalBot.__init__(self, wiki, debug)
        self.botname = 'MagazinesGL'
        self.searcher_pages = PetScan()
        self.searcher_indexes = PetScan()
        self.regex_page = re.compile('Die_Gartenlaube_\((\d{4})\)_([^\.]*?)\.(?:jpg|JPG)')
        self.regex_index = re.compile('Die_Gartenlaube_\((\d{4})\)')
        self.regex_magazine_in_index = re.compile('((?:Heft|Halbheft) (?:\{\{0\}\})?\d{1,2}:?.*?(?:\n\n|\Z))', re.DOTALL)
        self.regex_page_in_magazine = re.compile('_([_\w]{1,9}).(?:jpg|JPG)')
        self.regex_magazine_number_in_magazine = re.compile('(?:Heft|Halbheft) (?:\{\{0\}\})?(\d{1,2}):?')

    def __enter__(self):
        CanonicalBot.__enter__(self)
        if not self.data:
            self.data = {'pages':{}, 'indexes':{}}

    def run(self):
        self.indexes = self.search_indexes()
        self.lemmas = self.search_pages()
        tempdata_pages = {'1897': ['556', '805'], '1884': ['504'], '1888': ['861', '862', '863', '866', '867', '878', '879'], '1881': ['440'], '1882': ['398'], '1869': ['630'], '1876': ['355', '398', '572'], '1868': ['555'], '1870': ['718'], '1858': ['111'], '1886': ['288'], '1875': ['325', '326', '327', '328', '335', '338', '339', '340', '341', '342', '639', '843'], '1856': ['003', '047', '065', '103', '124', '148', '149', '155', '161', '109', '110', '179'], '1892': ['725'], '1879': ['031'], '1862': ['800'], '1880': ['640'], '1864': ['062', 'p_5', '064'], '1863': ['485']}
        #self.process_pages(tempdata_pages)
        self.process_indexes()
        tempdata_magzines = self.process_actual_pages(tempdata_pages)
        wait = 0

    def process_pages(self, tempdata):
        for idx, lemma in enumerate(self.lemmas):
            try:
                hit = self.regex_page.search(lemma['title'])
                year = hit.group(1)
                page = hit.group(2)
                if not year in self.data['pages'].keys():
                    self.data['pages'][year] = {}
                proofread_lemma = ProofreadPage(self.wiki, 'Seite:{}'.format(lemma['title']))
                self.logger.debug('{idx}/{sum} Page {page}({year}) has quality level {level} _ [[Seite:{title}]]'
                                  .format(idx=idx,
                                          sum=len(self.lemmas),
                                          page=page,
                                          year=year,
                                          level=proofread_lemma.quality_level,
                                          title=lemma['title']))
                self.data['pages'][year][page] = proofread_lemma.quality_level
                if not year in tempdata.keys():
                    tempdata[year] = []
                tempdata[year].append(page)
            except:
                self.logger.error("wasn't able to process {}".format(lemma['title']))

    def process_indexes(self):
        for idx, index in enumerate(self.indexes):
            index_lemma = IndexPage(self.wiki, 'Index:{}'.format(index['title']))
            self.logger.info('{idx}/{sum} [[Index:{index}]]'
                              .format(idx=idx + 1,
                                      sum=len(self.indexes),
                                      index=index['title']))
            magazines = self.regex_magazine_in_index.findall(index_lemma.text)
            hit_year = self.regex_index.search(index['title'])
            year = hit_year.group(1)
            if not year in self.data['indexes'].keys():
                self.data['indexes'][year] = {}
            for magazine in magazines:
                pages = self.regex_page_in_magazine.findall(magazine)
                hit_number = self.regex_magazine_number_in_magazine.findall(magazine)
                number = int(hit_number[0])
                self.data['indexes'][year][number] = pages

    def process_actual_pages(self, dictionary_of_new_pages):
        tempdata_magzines = {}
        for idx, year in enumerate(dictionary_of_new_pages):
            set_of_pages = set(dictionary_of_new_pages[year])
            tempdata_magzines[year] = set()
            dictionary_of_magazines = self.data['indexes'][year]
            for magazine in dictionary_of_magazines:
                set_of_potential_pages = set(dictionary_of_magazines[magazine])
                if set_of_potential_pages.intersection(set_of_pages):
                    tempdata_magzines[year].add(magazine)
        return tempdata_magzines

    def make_magazines(self, dictionary_of_magazines_by_year):
        for year in dictionary_of_magazines_by_year:
            magazines = dictionary_of_magazines_by_year[year]
            for magazine in magazines:
                lemma = Page(self.wiki, 'Benutzer:THEbotIT/Test')
                #test if magazine is the last in the year
                new_text = self.make_magazine(year, magazine)

    def make_magazine(self, year, magazine, quality, list_of_pages, last=False):
        string_list = []
        string_list.append('{{Textdaten\n')
        if magazine > 1:
            string_list.append('|VORIGER=Die Gartenlaube ({year:d})/Heft {magazine:d}\n'.format(year=year,
                                                                                                magazine=magazine-1))
        else:
            string_list.append('|VORIGER=\n')
        if last:
            string_list.append('|NÄCHSTER=\n')
        else:
            string_list.append('|NÄCHSTER=Die Gartenlaube ({year:d})/Heft {magazine:d}\n'.format(year=year,
                                                                                                magazine=magazine+1))
        string_list.append("|AUTOR=Verschiedene\n|TITEL=[[Die Gartenlaube]]\n|SUBTITEL=''Illustrirtes Familienblatt''\n|HERKUNFT=off\n")
        if year < 1962:
            string_list.append('|HERAUSGEBER=[[Ernst Keil]]\n')

    def search_indexes(self):
        self.searcher_indexes.add_positive_category('Die Gartenlaube')
        self.searcher_indexes.add_positive_category('Index')
        self.searcher_indexes.set_regex_filter('.*Die Gartenlaube \(\d{4}\)')
        self.searcher_indexes.set_timeout(60)
        #if self.last_run and self.last_run['succes'] and self.data:
        if False:
            self.create_timestamp_for_search(self.searcher_indexes)
        elif self.debug:
            self.create_timestamp_for_search(self.searcher_indexes, 5)
        return self.searcher_indexes.run()

    def search_pages(self):
        self.searcher_pages.add_positive_category('Die Gartenlaube')
        self.searcher_pages.add_namespace('Seite')
        self.searcher_pages.set_search_depth(1)
        self.searcher_pages.set_timeout(60)
        if self.last_run and self.last_run['succes'] and self.data:
            self.create_timestamp_for_search(self.searcher_pages)
        elif self.debug:
            self.create_timestamp_for_search(self.searcher_pages, 0)
        return self.searcher_pages.run()


if __name__ == "__main__":
    with open('../password.pwd') as password_file:
        password = load_password(password_file)
        wiki = Site(code= 'de', fam= 'wikisource', user='THEbotIT')
        login = LoginManager(site=wiki, password=password)
        login.login()

    bot = MagazinesGL(wiki=wiki, debug=True)
    with SaveExecution(bot):
        bot.run()
