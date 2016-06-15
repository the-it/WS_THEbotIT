__author__ = 'erik'

import sys
import os
import pywikibot
import json
import re
import traceback
import time
import datetime
from datetime import timedelta

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + os.sep + os.pardir + os.sep + os.pardir + os.sep )

from tools.catscan.catscan import CatScan
from tools.date_conversion import DateConversion
from tools.wiki_template_handler.template_handler import TemplateHandler
from tools.bots import CanonicalBot, SaveExecution

class AuthorList(CanonicalBot):
    def __init__(self):
        self.botname = 'AuthorList'
        self.searcher = CatScan()
        self.wiki = pywikibot.Site()
        self.string_list = []

    def __dig_up_data(self):
        self.timestamp = None

    def run(self):
        lemma_list = self.run_searcher()
        self.build_database(lemma_list)
        dump = pywikibot.Page(self.wiki, 'Benutzer:THEbotIT/{}'.format(self.botname))
        dump.text =  self.convert_to_table()
        dump.save('die Liste wurde auf den aktuellen Stand gebracht.', botflag=True)

    def run_searcher(self):
        # was the last run successful
        if self.last_run and self.last_run['succes'] and self.data:
            start_of_search = self.last_run['timestamp'] - timedelta(days=1)
            self.searcher.last_change_after(int(start_of_search.strftime('%Y')),
                                            int(start_of_search.strftime('%m')),
                                            int(start_of_search.strftime('%d')) )
            self.logger.info('The date {} is set to the argument "after".'.format(start_of_search.strftime("%d.%m.%Y")))
        #elif __debug__:
        elif False:
            yesterday = datetime.datetime.now() - timedelta(days=20)
            self.searcher.last_change_after(int(yesterday.strftime('%Y')),
                                            int(yesterday.strftime('%m')),
                                            int(yesterday.strftime('%d')) )
        else:
            self.logger.warning('There was no timestamp found of the last run, so the argument "after" is not set.')
        self.searcher.add_namespace(0)  # search in main namespace
        self.searcher.add_positive_category('Autoren')
        self.searcher.add_yes_template('Personendaten')
        self.searcher.get_wikidata_items()

        self.logger.debug(self.searcher)

        return self.searcher.run()

    def build_database(self, lemma_list):
        for idx, author in enumerate(lemma_list):
            self.logger.debug('{}/{} {}'.format(idx + 1, len(lemma_list), author['title']))
            # delete preexisting data of this author
            try:
                del self.data[str(author['id'])]
            except:
                if self.last_run and self.last_run['succes']:
                    self.logger.warning("Can't delete old entry of {}".format(author['title']))

            dict_author = {'title': author['title']}
            # extract the Personendaten-block form the wikisource page
            page = pywikibot.Page(self.wiki, author['title'])
            try:
                try:
                    personendaten = re.search('\{\{Personendaten(?:.|\n)*?\n\}\}\n', page.text).group()
                except:
                    self.logger.error('No valid block "Personendaten" was found.')
                    personendaten = None
                if personendaten:
                    template_extractor = TemplateHandler(personendaten)
                    dict_author.update({'name': template_extractor.get_parameter('NACHNAME')['value']})
                    dict_author.update({'first_name': template_extractor.get_parameter('VORNAMEN')['value']})
                    dict_author.update({'birth': template_extractor.get_parameter('GEBURTSDATUM')['value']})
                    dict_author.update({'death': template_extractor.get_parameter('STERBEDATUM')['value']})
                    dict_author.update({'description': template_extractor.get_parameter('KURZBESCHREIBUNG')['value']})
                    dict_author.update({'synonyms': template_extractor.get_parameter('ALTERNATIVNAMEN')['value']})
                    try:
                        dict_author.update({'sortkey': template_extractor.get_parameter('SORTIERUNG')['value']})
                        if dict_author['sortkey'] == '':
                            raise ValueError
                    except:
                        self.logger.debug('there is no sortkey for {}.'.format(author['title']))
                        # make a dummy key
                        dict_author['sortkey'] = dict_author['name'] + ', ' + dict_author['first_name']
                    dict_author.update({'wikidata' : author['q']})
                    self.data.update({author['id']: dict_author})
            except Exception as e:
                self.logger.error(traceback.format_exc())
                self.logger.error('author {} have a problem'.format(author['title']))


    def convert_to_table(self):
        # make a list of lists
        self.logger.info('Start compiling.')
        list_authors = []
        for key in self.data:
            author_dict = self.data[key]
            list_author = []
            list_author.append(author_dict['sortkey']) #0
            list_author.append(author_dict['title'].replace('_', ' ')) #1
            list_author.append(author_dict['name'])#2
            list_author.append(author_dict['first_name'])#3
            list_author.append(author_dict['birth'])#4
            try:
                list_author.append(str(DateConversion(author_dict['birth'])))#5
            except:
                self.logger.error('Can´t compile sort key for birth: {}'.format(author_dict['birth']))
                list_author.append('!-00-00')  # 5
            list_author.append(author_dict['death']) #6
            try:
                list_author.append(str(DateConversion(author_dict['death'])))#7
            except:
                self.logger.error('Can´t compile sort key for death: {}'.format(author_dict['death']))
                list_author.append('!-00-00')  # 7
            list_author.append(author_dict['description'])#8
            list_authors.append(list_author)
        # sorting the list
        self.logger.info('Start sorting.')
        list_authors.sort(key = lambda x: x[0])

        self.logger.info('Start printing.')
        self.string_list.append('Diese Liste der Autoren enthält alle {}<ref>Stand: {dt.day}.{dt.month}.{dt.year}, {dt.hour}:{dt.minute} (UTC)</ref> Autoren, zu denen in Wikisource eine Autorenseite existiert.'.format(len(self.data), dt = datetime.datetime.now()))
        self.string_list.append('Die Liste kann mit den Buttons neben den Spaltenüberschriften nach der jeweiligen Spalte sortiert werden.')
        self.string_list.append('<!--')
        self.string_list.append('Diese Liste wurde durch ein Computerprogramm erstellt, das die Daten verwendet, die aus den Infoboxen auf den Autorenseiten stammen.')
        self.string_list.append('Sollten daher Fehler vorhanden sein, sollten diese jeweils dort korrigiert werden.')
        self.string_list.append('-->')
        self.string_list.append('{| class="wikitable sortable"')
        self.string_list.append('! Name')
        self.string_list.append('! Name -Sortkey')
        self.string_list.append('! data-sort-type="text" | Geb.-datum')
        self.string_list.append('! data-sort-type="text" | Geb.-Sortkey')
        self.string_list.append('! data-sort-type="text" | Tod.-datum')
        self.string_list.append('! data-sort-type="text" | Tod.-Sortkey')
        self.string_list.append('! Beschreibung')
        for list_author in list_authors:
            self.string_list.append('|-')
            self.string_list.append('|{}, {}'.format(list_author[2], list_author[3]))
            self.string_list.append('| {}'.format(list_author[0]))
            self.string_list.append('| {}'.format(list_author[4]))
            self.string_list.append('| {}'.format(list_author[5]))
            self.string_list.append('| {}'.format(list_author[6]))
            self.string_list.append('| {}'.format(list_author[7]))
            #self.string_list.append('| {}'.format(list_author[8]))
        self.string_list.append('|}')
        self.string_list.append('')
        self.string_list.append('== Anmerkungen ==')
        self.string_list.append('<references/>')
        self.string_list.append('')
        self.string_list.append('{{SORTIERUNG: Autoren  # Liste der}}')
        self.string_list.append('[[Kategorie:Listen]]')
        self.string_list.append('[[Kategorie:Autoren |!]]')

        return '\n'.join(self.string_list)


if __name__ == "__main__":
    bot = AuthorList()
    with SaveExecution(bot):
        bot.run()
