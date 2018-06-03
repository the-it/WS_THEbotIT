from datetime import datetime
import re
from typing import Iterator

from pywikibot import Page, Site
from pywikibot.proofreadpage import ProofreadPage, IndexPage
from tools.catscan import PetScan
from tools.bots import CanonicalBot, BotException


def search_for_refs(text):
    ref = []
    if re.search(r'<ref>', text):
        ref.append('ref')
    elif re.search(r'\{\{CRef\|\|', text):
        ref.append('ref')
    hit = re.findall('[Gg]roup ?= ?(\"[^\"]*\"|[^\"> ]{1,10})', text)
    if hit:
        for entry in hit:
            group = entry.strip("\"")
            if group not in ref:
                ref.append(group)
    hit = re.findall(r'\{\{CRef\|([^\|]{1,10})\|', text)
    if hit:
        for entry in hit:
            if entry not in ref:
                ref.append(entry)
    return ref


class GlCreateMagazine(CanonicalBot):
    def __init__(self, wiki, debug):
        CanonicalBot.__init__(self, wiki, debug)
        self.searcher_pages = PetScan()
        self.searcher_indexes = PetScan()
        self.regex_page = re.compile(r'Die_Gartenlaube_\((\d{4})\)_([^\.]*?)\.(?:jpg|JPG)')
        self.regex_index = re.compile(r'Die_Gartenlaube_\((\d{4})\)')
        self.regex_magazine_in_index = \
            re.compile(r'((?:Heft|Halbheft) (?:\{\{0\}\})?\d{1,2}:.*?(?:\n\n|\Z))', re.DOTALL)
        self.regex_page_in_magazine = re.compile(r'_([_\w]{1,9}).(?:jpg|JPG)')
        self.regex_number_in_index = re.compile(r'(?:Heft|Halbheft) (?:\{\{0\}\})?(\d{1,2}):?')
        self.new_data_model = datetime(year=2017, month=11, day=11, hour=12)
        self.lemmas = None

    def __enter__(self):
        CanonicalBot.__enter__(self)
        if not self.data:
            self.data.assign_dict({'pages': {}, 'indexes': {}})
        return self

    def task(self):
        self.lemmas = self.search_pages()
        temp_data_pages = {}
        self.process_indexes()
        self.process_pages(temp_data_pages)
        temp_data_magazines = self.process_actual_pages(temp_data_pages)
        self.make_magazines(temp_data_magazines)
        return True

    def process_pages(self, temp_data):
        for idx, lemma in enumerate(self.lemmas):
            try:
                hit = self.regex_page.search(lemma['title'])
                year = hit.group(1)
                page = hit.group(2)
                if year not in self.data['pages'].keys():
                    self.data['pages'][year] = {}
                proofread_lemma = ProofreadPage(self.wiki, 'Seite:{}'.format(lemma['title']))
                if self.debug:
                    self.logger.debug('{idx}/{sum} Page {page}({year}) '
                                      'has quality level {level} _ Seite:{title}'
                                      .format(idx=idx + 1,
                                              sum=len(self.lemmas),
                                              page=page,
                                              year=year,
                                              level=proofread_lemma.quality_level,
                                              title=lemma['title']))
                ref = search_for_refs(proofread_lemma.text)
                page_dict = {'q': proofread_lemma.quality_level}
                if ref:
                    self.logger.debug('There are refs ({refs}) @ {year}, {page}'.format(refs=ref,
                                                                                        page=page,
                                                                                        year=year))
                    page_dict.update({'r': ref})
                self.data['pages'][year][page] = page_dict
                if year not in temp_data.keys():
                    temp_data[year] = []
                temp_data[year].append(page)
            except Exception as error:  # pylint: disable=broad-except
                self.logger.error("wasn't able to process {}, error: {}"
                                  .format(lemma['title'], error))

    def process_indexes(self):
        for index_lemma, index_page in self._get_indexes():
            self.logger.debug("[[Index:{}]]".format(index_lemma))
            magazines = self.regex_magazine_in_index.findall(index_page.text)
            hit_year = self.regex_index.search(index_lemma)
            year = hit_year.group(1)
            if year not in self.data['indexes'].keys():
                self.data['indexes'][year] = {}
            for magazine in magazines:
                pages = self.regex_page_in_magazine.findall(magazine)
                hit_number = self.regex_number_in_index.findall(magazine)
                number = int(hit_number[0])
                self.data['indexes'][year][number] = pages

    def process_actual_pages(self, dictionary_of_new_pages):
        tempdata_magzines = {}
        for year in dictionary_of_new_pages:
            set_of_pages = set(dictionary_of_new_pages[year])
            tempdata_magzines[year] = set()
            try:
                dictionary_of_magazines = self.data['indexes'][year]
            except KeyError:
                raise BotException('The list of indexes is incorrect, {year} is missing.'
                                   .format(year=year))
            for magazine in dictionary_of_magazines:
                set_of_potential_pages = set(dictionary_of_magazines[magazine])
                if set_of_potential_pages.intersection(set_of_pages):
                    tempdata_magzines[year].add(magazine)
        return tempdata_magzines

    def make_magazines(self, dictionary_of_magazines_by_year):
        for idx_year, year in enumerate(dictionary_of_magazines_by_year):
            magazines = dictionary_of_magazines_by_year[year]
            self.logger.debug('make_mag_year {idx}/{len}'
                              .format(idx=idx_year + 1, len=len(dictionary_of_magazines_by_year)))
            for idx_mag, magazine in enumerate(magazines):
                self.logger.debug('make_mag_mag {idx}/{len} ... issue:{year}/{mag}'
                                  .format(idx=idx_mag + 1, len=len(magazines),
                                          year=year, mag=magazine))
                if year == '1986' and magazine == '31':
                    self.logger.warning('There is magazine 1986, 31, '
                                        'this is special, no creating here')
                    continue
                if self.debug:
                    lemma = Page(self.wiki, 'Benutzer:THEbotIT/Test')
                else:
                    lemma = Page(self.wiki, 'Die Gartenlaube ({year})/Heft {magazine:d}'
                                 .format(year=year, magazine=int(magazine)))
                new_text = self.make_magazine(year, magazine)
                if new_text:
                    if new_text != lemma.text:
                        self.logger.debug('Print [[Die Gartenlaube ({year})/Heft {magazine}]].'
                                          .format(year=year, magazine=magazine))
                        if lemma.text != '':
                            lemma.text = new_text
                            lemma.save('Automatische Aktualisierung des Heftes', botflag=True)
                        else:
                            lemma.text = new_text
                            lemma.save('automatische Hefterstellung', botflag=True)
                    else:
                        self.logger.debug('Keine Änderung im Text ({year}/{magazine}).'
                                          .format(year=year, magazine=magazine))

    def make_magazine(self, year, magazine):
        last_magazine = True
        try:
            for key in self.data['indexes'][year].keys():
                if int(key) > int(magazine):
                    last_magazine = False
                    break
        except KeyError:
            raise BotException('The list of indexes is incorrect, {year} is missing.'
                               .format(year=year))
        try:
            list_of_pages = self.data['indexes'][year][magazine]
        except KeyError:
            raise BotException('The list of indexes is incorrect, '
                               'year:{year} or mag:{mag} is missing.'
                               .format(year=year, mag=magazine))
        quality = 4
        for page in list_of_pages:
            try:
                if self.data['pages'][year][page]['q'] == 0:
                    page_quality = 4
                else:
                    page_quality = self.data['pages'][year][page]['q']
                if page_quality < quality:
                    quality = page_quality
                if quality < 3:
                    self.logger.debug('The quality of {year}/{magazine} is too poor.'
                                      .format(year=year, magazine=magazine))
                    return None
            except KeyError:
                self.logger.warning('The list of pages is incorrect, '
                                    'year:{year} or page:{page} is missing.'
                                    .format(year=year, page=page))
                return None
        return self.make_magazine_text(year, magazine, quality, list_of_pages, last_magazine)

    @staticmethod
    def convert_page_no(page: str):
        while True:
            if page[0] == "0":
                page = page[1:]
            else:
                break
        return page.replace('_', ' ')

    def make_magazine_text(self, year, magazine, quality, list_of_pages, last):
        # pylint: disable=too-many-arguments,too-many-branches
        magazine = int(magazine)
        year = int(year)
        string_list = list()
        string_list.append('<!--Diese Seite wurde automatisch durch einen Bot erstellt. '
                           'Wenn du einen Fehler findest oder eine Änderung wünscht, '
                           'benachrichtige bitte den Betreiber, THE IT, des Bots.-->\n'
                           '{{Textdaten\n')
        if magazine > 1:
            string_list.append('|VORIGER=Die Gartenlaube ({year:d})/Heft {magazine:d}\n'
                               .format(year=year, magazine=magazine - 1))
        else:
            string_list.append('|VORIGER=\n')
        if last:
            string_list.append('|NÄCHSTER=\n')
        else:
            string_list.append('|NÄCHSTER=Die Gartenlaube ({year:d})/Heft {magazine:d}\n'
                               .format(year=year, magazine=magazine + 1))
        string_list.append("|AUTOR=Verschiedene\n|TITEL=[[Die Gartenlaube]]\n"
                           "|SUBTITEL=''Illustrirtes Familienblatt''\n|HERKUNFT=off\n")
        if year < 1863:
            string_list.append('|HERAUSGEBER=[[Ferdinand Stolle]]\n')
        elif (year < 1878) or (year == 1878 and magazine < 14):
            string_list.append('|HERAUSGEBER=[[Ernst Keil]]\n')
        elif year < 1885:
            string_list.append('|HERAUSGEBER=Ernst Ziel\n')
        else:
            string_list.append('|HERAUSGEBER=Adolf Kröner\n')
        string_list.append('|ENTSTEHUNGSJAHR={year:d}\n|ERSCHEINUNGSJAHR={year:d}\n'
                           '|ERSCHEINUNGSORT=Leipzig\n|VERLAG=Ernst Keil\n'
                           '|WIKIPEDIA=Die Gartenlaube\n'.format(year=year))
        if year == 1873:
            extension = "JPG"
        else:
            extension = "jpg"
        string_list.append('|BILD=Die Gartenlaube ({year:d}) {page1}.{extension}\n'
                           .format(year=year, page1=list_of_pages[0], extension=extension))
        string_list.append('|QUELLE=[[commons:category:Gartenlaube ({year})|commons]]\n'
                           .format(year=year))
        if quality == 4:
            string_list.append('|BEARBEITUNGSSTAND=fertig\n')
        else:
            string_list.append('|BEARBEITUNGSSTAND=korrigiert\n')
        string_list.append('|INDEXSEITE=Die Gartenlaube ({year})\n}}}}\n\n'
                           '{{{{BlockSatzStart}}}}\n__TOC__\n'.format(year=year))
        ref = []
        for page in list_of_pages:
            page_format = self.convert_page_no(page)
            string_list.append(
                '{{{{SeitePR|{page_format}|Die Gartenlaube ({year}) {page}.{extension}}}}}\n'
                .format(year=year, page_format=page_format, page=page, extension=extension))
            try:
                page_dict = self.data['pages'][str(year)][page]
                if 'r' in page_dict.keys():
                    if 'ref' in page_dict['r']:
                        if 'ref' not in ref:
                            ref.append('ref')
                    for ref_type in page_dict['r']:
                        if (ref_type != 'ref') and (ref_type not in ref):
                            ref.append(ref_type)
            except KeyError:
                self.logger.error('The list of pages is incorrect, '
                                  'year:{year} or page:{page} is missing.'
                                  .format(year=year, page=page))
                return None
        if 'ref' in ref:
            string_list.append('{{references|x}}\n')
        for ref_type in ref:
            if ref_type != 'ref':
                string_list.append('{{{{references|TIT|{ref}}}}}\n'.format(ref=ref_type))
        string_list.append('{{{{BlockSatzEnd}}}}\n\n[[Kategorie:Deutschland]]\n'
                           '[[Kategorie:Neuhochdeutsch]]\n[[Kategorie:Illustrierte Werke]]\n'
                           '[[Kategorie:Die Gartenlaube ({year:d}) Hefte| {magazine:02d}]]\n'
                           .format(year=year, magazine=magazine))
        string_list.append('[[Kategorie:{year}0er Jahre]]\n\n'.format(year=str(year)[0:3]))
        return ''.join(string_list)

    def _get_indexes(self) -> Iterator[IndexPage]:
        self.searcher_indexes.add_positive_category('Die Gartenlaube')
        self.searcher_indexes.add_positive_category('Index')
        self.searcher_indexes.set_regex_filter(r'.*Die Gartenlaube \(\d{4}\)')
        self.searcher_indexes.set_timeout(60)
        for index in self.searcher_indexes.run():
            yield index["title"], IndexPage(self.wiki, 'Index:{}'.format(index['title']))

    def search_pages(self):
        self.searcher_pages.add_positive_category('Die Gartenlaube')
        self.searcher_pages.add_namespace('Seite')
        self.searcher_pages.set_search_depth(1)
        self.searcher_pages.set_timeout(60)
        if self.last_run_successful or self.debug:
            delta = (self.timestamp.start_of_run - self.timestamp.last_run).days
            if self.debug:
                delta = 10
            start_of_search = self.create_timestamp_for_search(delta)
            self.searcher_pages.last_change_after(start_of_search)
            self.logger.info('The date {} is set to the argument "after".'
                             .format(start_of_search.strftime("%d.%m.%Y")))
        return self.searcher_pages.run()


if __name__ == "__main__":
    WIKI = Site(code='de', fam='wikisource', user='THEbotIT')
    with GlCreateMagazine(wiki=WIKI, debug=True) as bot:
        bot.run()
