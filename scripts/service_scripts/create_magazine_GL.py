import sys
import os
import re

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + os.sep + os.pardir + os.sep + os.pardir + os.sep )

from pywikibot import Site, Page
from pywikibot.proofreadpage import ProofreadPage, IndexPage
from tools.catscan import PetScan
from tools.bots import CanonicalBot, SaveExecution, BotExeption

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
        tempdata_pages = {}
        self.process_indexes()
        self.process_pages(tempdata_pages)
        tempdata_magzines = self.process_actual_pages(tempdata_pages)
        self.make_magazines(tempdata_magzines)

    def process_pages(self, tempdata):
        for idx, lemma in enumerate(self.lemmas):
            try:
                hit = self.regex_page.search(lemma['title'])
                year = hit.group(1)
                page = hit.group(2)
                if not year in self.data['pages'].keys():
                    self.data['pages'][year] = {}
                proofread_lemma = ProofreadPage(self.wiki, 'Seite:{}'.format(lemma['title']))
                self.logger.debug('{idx}/{sum} Page {page}({year}) has quality level {level} _ Seite:{title}'
                                  .format(idx=idx + 1,
                                          sum=len(self.lemmas),
                                          page=page,
                                          year=year,
                                          level=proofread_lemma.quality_level,
                                          title=lemma['title']))
                ref = self.search_for_refs(proofread_lemma.text)
                if ref[0]:
                    self.logger.debug('There are refs on Page {page}({year})'
                                      .format(page=page,
                                              year=year))
                if ref[1]:
                    self.logger.debug('There are refs(WS) on Page {page}({year})'
                                      .format(page=page,
                                              year=year))
                self.data['pages'][year][page] = [proofread_lemma.quality_level, ref[0], ref[1]]
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
            try:
                dictionary_of_magazines = self.data['indexes'][year]
            except KeyError:
                raise BotExeption('The list of indexes is incorrect, {year} is missing.'.format(year=year))
            for magazine in dictionary_of_magazines:
                set_of_potential_pages = set(dictionary_of_magazines[magazine])
                if set_of_potential_pages.intersection(set_of_pages):
                    tempdata_magzines[year].add(magazine)
        return tempdata_magzines

    def make_magazines(self, dictionary_of_magazines_by_year):
        for idx_year, year in enumerate(dictionary_of_magazines_by_year):
            magazines = dictionary_of_magazines_by_year[year]
            self.logger.info('make_mag_year {idx}/{len}'.format(idx=idx_year + 1,
                                                                len=len(dictionary_of_magazines_by_year)))
            for idx_mag, magazine in enumerate(magazines):
                self.logger.info('make_mag_mag {idx}/{len} ... issue:{year}/{mag}'.format(idx=idx_mag + 1,
                                                                                          len=len(magazines),
                                                                                          year=year,
                                                                                          mag=magazine))
                if self.debug:
                    lemma = Page(self.wiki, 'Benutzer:THEbotIT/Test')
                else:
                    lemma = Page(self.wiki, 'Die Gartenlaube ({year})/Heft {magazine:d}'.format(year=year,
                                                                                                magazine=int(magazine)))
                new_text = self.make_magazine(year, magazine)
                if new_text:
                    if new_text != lemma.text:
                        if lemma.text != '':
                            lemma.text = new_text
                            lemma.save('automatisches Update des Heftes', botflag=True)
                        else:
                            lemma.text = new_text
                            lemma.save('automatisches Hefterstellung', botflag=True)
                    else:
                        self.logger.info('Keine Änderung im Text ({year}/{magazine}).'.format(year=year,
                                                                                              magazine=magazine))

    def make_magazine(self, year, magazine):
        last_magazine = True
        try:
            for key in self.data['indexes'][year].keys():
                if int(key) > int(magazine):
                    last_magazine = False
                    break
        except KeyError:
            raise BotExeption('The list of indexes is incorrect, {year} is missing.'.format(year=year))
        try:
            list_of_pages = self.data['indexes'][year][magazine]
        except KeyError:
            raise BotExeption('The list of indexes is incorrect, year:{year} or mag:{mag} is missing.'
                              .format(year=year, mag=magazine))
        quality = 4
        for page in list_of_pages:
            try:
                if (self.data['pages'][year][page][0] == 0) and quality == 4:
                    quality = 4
                elif self.data['pages'][year][page][0] < quality:
                    quality = self.data['pages'][year][page][0]
                if quality < 3:
                    self.logger.info('The quality of {year}/{magazine} is too poor.'.format(year=year, magazine=magazine))
                    return None
            except KeyError:
                self.logger.warning('The list of pages is incorrect, year:{year} or page:{page} is missing.'
                                    .format(year=year, page=page))
                return None
        return self.make_magazine_text(year, magazine, quality, list_of_pages, last_magazine)

    def convert_page_no(self, page:str):
        while True:
            if page[0] == "0":
                page = page[1:]
            else:
                break
        return page.replace('_', ' ')

    def search_for_refs(self, text):
        ref = 0
        ref_WS = 0
        if re.search('<ref>', text):
            ref = 1
        elif re.search('\{\{CRef\|\|', text):
            ref = 1
        if re.search('<ref .*?WS', text):
            ref_WS = 1
        elif re.search('\{\{CRef\|WS\|', text):
            ref_WS = 1
        return [ref, ref_WS]

    def make_magazine_text(self, year, magazine, quality, list_of_pages, last):
        magazine = int(magazine)
        year = int(year)
        string_list = []
        string_list.append('<!--Diese Seite wurde automatisch durch einen Bot erstellt. Wenn du einen Fehler findest oder eine Änderung wünscht, benachrichtige bitte den Betreiber, THE IT, des Bots.-->\n')
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
        string_list.append("|AUTOR=Verschiedene\n")
        string_list.append("|TITEL=[[Die Gartenlaube]]\n")
        string_list.append("|SUBTITEL=''Illustrirtes Familienblatt''\n")
        string_list.append("|HERKUNFT=off\n")
        if year < 1963:
            string_list.append('|HERAUSGEBER=[[Ferdinand Stolle]]\n')
        elif (year < 1878) or (year == 1878 and magazine < 14):
            string_list.append('|HERAUSGEBER=[[Ernst Keil]]\n')
        elif year < 1885 :
            string_list.append('|HERAUSGEBER=Ernst Ziel\n')
        else:
            string_list.append('|HERAUSGEBER=Adolf Kröner\n')
        string_list.append('|ENTSTEHUNGSJAHR={year:d}\n'.format(year=year))
        string_list.append('|ERSCHEINUNGSJAHR={year:d}\n'.format(year=year))
        string_list.append('|ERSCHEINUNGSORT=Leipzig\n')
        string_list.append('|VERLAG=Ernst Keil\n')
        string_list.append('|WIKIPEDIA=Die Gartenlaube\n')
        string_list.append('|BILD=Die Gartenlaube ({year:d}) {page1}.jpg\n'.format(year=year, page1=list_of_pages[0]))
        string_list.append('|QUELLE=[[commons:category:Gartenlaube ({year})|commons]]\n'.format(year=year))
        if quality == 4:
            string_list.append('|BEARBEITUNGSSTAND=fertig\n')
        else:
            string_list.append('|BEARBEITUNGSSTAND=korrigiert\n')
        string_list.append('|INDEXSEITE=Die Gartenlaube ({year})\n'.format(year=year))
        string_list.append('}}\n\n')
        string_list.append('{{BlockSatzStart}}\n')
        string_list.append('__TOC__\n')
        ref = [False, False]
        for page in list_of_pages:
            page_format = self.convert_page_no(page)
            string_list.append('{{{{SeitePR|{page_format}|Die Gartenlaube ({year}) {page}.jpg}}}}\n'
                               .format(year=year,
                                       page_format=page_format,
                                       page=page))
            for idx, ref_type in enumerate(ref):
                if not ref_type:
                    try:
                        if self.data['pages'][str(year)][page][idx + 1]:
                            ref[idx] = True
                    except KeyError:
                        self.logger.error('The list of pages is incorrect, year:{year} or page:{page} is missing.'
                                          .format(year=year, page=page))
                        return None
        if ref[0]:
            string_list.append('{{references|x}}\n')
        if ref[1]:
            string_list.append('{{references|TIT|WS}}\n')
        string_list.append('{{BlockSatzEnd}}\n\n[[Kategorie:Deutschland]]\n[[Kategorie:Neuhochdeutsch]]\n[[Kategorie:Illustrierte Werke]]\n')
        string_list.append('[[Kategorie:Die Gartenlaube ({year:d}) Hefte| {magazine:02d}]]\n'.format(year=year, magazine=magazine))
        string_list.append('[[Kategorie:{year}0er Jahre]]\n'.format(year=str(year)[0:3]))
        string_list.append('\n')
        return ''.join(string_list)

    def search_indexes(self):
        self.searcher_indexes.add_positive_category('Die Gartenlaube')
        self.searcher_indexes.add_positive_category('Index')
        self.searcher_indexes.set_regex_filter('.*Die Gartenlaube \(\d{4}\)')
        self.searcher_indexes.set_timeout(60)
        if self.last_run and self.last_run['succes'] and self.data:
        #if False:
            delta = (self.timestamp_start - self.last_run['timestamp']).days
            self.create_timestamp_for_search(self.searcher_indexes, delta)
        elif self.debug:
        #elif False:
            self.create_timestamp_for_search(self.searcher_indexes, 5)
        return self.searcher_indexes.run()

    def search_pages(self):
        self.searcher_pages.add_positive_category('Die Gartenlaube')
        self.searcher_pages.add_namespace('Seite')
        self.searcher_pages.set_search_depth(1)
        self.searcher_pages.set_timeout(60)
        if self.last_run and self.last_run['succes'] and self.data:
        #if False:
            delta = (self.timestamp_start - self.last_run['timestamp']).days
            self.create_timestamp_for_search(self.searcher_pages, delta)
        elif self.debug:
        #elif False:
            self.create_timestamp_for_search(self.searcher_pages, 0)
        return self.searcher_pages.run()


if __name__ == "__main__":
    wiki = Site(code= 'de', fam= 'wikisource', user='THEbotIT')
    bot = MagazinesGL(wiki=wiki, debug=True)
    with SaveExecution(bot):
        bot.run()
