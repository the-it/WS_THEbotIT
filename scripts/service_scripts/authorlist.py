import sys
import os
import pywikibot
import re
import traceback
import datetime
from datetime import timedelta
from pywikibot.data.api import LoginManager

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + os.sep + os.pardir + os.sep + os.pardir + os.sep )

from tools.catscan import CatScan
from tools.date_conversion import DateConversion
from tools.template_handler import TemplateHandler
from tools.bots import CanonicalBot, SaveExecution
from tools.little_helpers import load_password

class AuthorList(CanonicalBot):
    def __init__(self, wiki):
        CanonicalBot.__init__(self, wiki)
        self.botname = 'AuthorList'
        self.searcher = CatScan()
        self.repo = self.wiki.data_repository()  # this is a DataSite object
        self.string_list = []
        self.match_property = re.compile('\{\{#property:P(\d{1,4})\}\}')
        self.number_to_month = {1: 'Januar',
                           2: 'Februar',
                           3: 'März',
                           4: 'April',
                           5: 'Mai',
                           6: 'Juni',
                           7: 'Juli',
                           8: 'August',
                           9: 'September',
                           10: 'Oktober',
                           11: 'November',
                           12: 'Dezember'}

    def run(self):
        lemma_list = self._run_searcher()
        self._build_database(lemma_list)
        if __debug__:
            dump = pywikibot.Page(self.wiki, 'Benutzer:THEbotIT/{}'.format(self.botname))
        else:
            dump = pywikibot.Page(self.wiki, 'Liste der Autoren')
        dump.text =  self._convert_to_table()
        dump.save('die Liste wurde auf den aktuellen Stand gebracht.', botflag=True)

    def _run_searcher(self):
        # was the last run successful
        #if __debug__:
        if False:
            yesterday = datetime.datetime.now() - timedelta(days=5)
            self.searcher.last_change_after(int(yesterday.strftime('%Y')),
                                            int(yesterday.strftime('%m')),
                                            int(yesterday.strftime('%d')))
        elif self.last_run and self.last_run['succes'] and self.data:
            start_of_search = self.last_run['timestamp'] - timedelta(days=1)
            self.searcher.last_change_after(int(start_of_search.strftime('%Y')),
                                            int(start_of_search.strftime('%m')),
                                            int(start_of_search.strftime('%d')) )
            self.logger.info('The date {} is set to the argument "after".'
                             .format(start_of_search.strftime("%d.%m.%Y")))
        else:
            self.logger.warning('There was no timestamp found of the last run, so the argument "after" is not set.')
        self.searcher.add_namespace(0)  # search in main namespace
        self.searcher.add_positive_category('Autoren')
        self.searcher.add_yes_template('Personendaten')
        self.searcher.get_wikidata_items()

        self.logger.debug(self.searcher)

        entries_to_search = self.searcher.run()
        #following entries are ignored by petscan
        entries_to_search.append({'title': "Karl_Löffler", 'q': 'Q1732245', 'id':'413038'})
        entries_to_search.append({'title': "Adolf_Wüllner", 'q': 'Q106820', 'id':'413022'})
        return entries_to_search

    def _build_database(self, lemma_list):
        for idx, author in enumerate(lemma_list):
            self.logger.debug('{}/{} {}'.format(idx + 1, len(lemma_list), author['title']))
            # delete preexisting data of this author
            try:
                del self.data[str(author['id'])]
            except:
                if self.last_run and self.last_run['succes']:
                    self.logger.info("Can't delete old entry of {}".format(author['title']))

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
                    #personendaten = re.sub('<ref.*?>.*?<\/ref>|<ref.*?\/>', '', personendaten)
                    #personendaten = re.sub('\{\{CRef|.*?(?:\{\{.*?\}\})?}}', '', personendaten)
                    template_extractor = TemplateHandler(personendaten)
                    dict_author.update({'name': template_extractor.get_parameter('NACHNAME')['value']})
                    dict_author.update({'first_name': template_extractor.get_parameter('VORNAMEN')['value']})
                    try:
                        dict_author.update({'birth': template_extractor.get_parameter('GEBURTSDATUM')['value']})
                    except:
                        dict_author.update({'birth': ""})
                        self.logger.warning("Templatehandler couldn't find a birthdate for: {}".format(author['title']))
                    try:
                        dict_author.update({'death': template_extractor.get_parameter('STERBEDATUM')['value']})
                    except:
                        dict_author.update({'death': ""})
                        self.logger.warning("Templatehandler couldn't find a deathdate for: {}".format(author['title']))
                    try:
                        dict_author.update({'description': template_extractor.get_parameter('KURZBESCHREIBUNG')['value']})
                    except:
                        dict_author.update({'description': ""})
                        self.logger.warning("Templatehandler couldn't find a description for: {}".format(author['title']))
                    try:
                        dict_author.update({'synonyms': template_extractor.get_parameter('ALTERNATIVNAMEN')['value']})
                    except:
                        dict_author.update({'synonyms': ""})
                        self.logger.warning("Templatehandler couldn't find synonyms for: {}".format(author['title']))
                    try:
                        dict_author.update({'sortkey': template_extractor.get_parameter('SORTIERUNG')['value']})
                        if dict_author['sortkey'] == '':
                            raise ValueError
                    except:
                        self.logger.debug('there is no sortkey for {}.'.format(author['title']))
                        # make a dummy key
                        dict_author['sortkey'] = dict_author['name'] + ', ' + dict_author['first_name']
                    try:
                        dict_author.update({'wikidata' : author['q']})
                    except:
                        self.logger.warning('The autor {} has no wikidata_item'.format(author['title']))
                    self.data.update({author['id']: dict_author})
            except Exception as e:
                self.logger.error(traceback.format_exc())
                self.logger.error('author {} have a problem'.format(author['title']))

    def _convert_to_table(self):
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

            for event in ['birth', 'death']:
                list_author.append(self._handle_birth_and_death(event, author_dict)) #4,6
                try:
                    list_author.append(str(DateConversion(list_author[-1])))#5,7
                except:
                    self.logger.error('Can´t compile sort key for {}: {}'.format(event, author_dict[event]))
                    list_author.append('!-00-00')  # 5,7
            list_author.append(author_dict['description'])#8
            list_authors.append(list_author)

        # sorting the list
        self.logger.info('Start sorting.')
        list_authors.sort(key = lambda x: x[0])
        for i in range(len(list_authors) - 1):
            if list_authors[i][0] == list_authors[i+1][0]:
                equal_count = 2
                while True:
                    if i+equal_count <= len(list_authors):
                        if list_authors[i][0] != list_authors[i+equal_count][0]:
                            break
                        equal_count += 1
                temp_list = list_authors[i:i+equal_count]
                temp_list.sort(key=lambda x: x[5])
                list_authors[i:i + equal_count] = temp_list

        self.logger.info('Start printing.')
        self.string_list.append('Diese Liste der Autoren enthält alle {count}<ref>Stand: {dt.day}.{dt.month}.{dt.year}, {dt.hour}:{minute} (UTC)</ref> Autoren, zu denen in Wikisource eine Autorenseite existiert.'
                                .format(count = len(self.data),
                                        minute = datetime.datetime.now().strftime('%M'),
                                        dt = datetime.datetime.now()))
        self.string_list.append('Die Liste kann mit den Buttons neben den Spaltenüberschriften nach der jeweiligen Spalte sortiert werden.')
        self.string_list.append('<!--')
        self.string_list.append('Diese Liste wurde durch ein Computerprogramm erstellt, das die Daten verwendet, die aus den Infoboxen auf den Autorenseiten stammen.')
        self.string_list.append('Sollten daher Fehler vorhanden sein, sollten diese jeweils dort korrigiert werden.')
        self.string_list.append('-->')
        self.string_list.append('{|class="wikitable sortable"')
        self.string_list.append('!style="width:20%"| Name')
        self.string_list.append('!data-sort-type="text" style="width:15%"| Geb.-datum')
        self.string_list.append('!data-sort-type="text" style="width:15%"| Tod.-datum')
        self.string_list.append('!class="unsortable" style="width:50%"| Beschreibung')
        for list_author in list_authors:
            self.string_list.append('|-')
            if list_author[2] and list_author[3]:
                self.string_list.append('|data-sort-value="{}"|[[{}|{}, {}]]'
                                        .format(list_author[0], list_author[1], list_author[2],list_author[3]))
            elif list_author[3]:
                self.string_list.append('|data-sort-value="{}"|[[{}|{}]]'
                                        .format(list_author[0], list_author[1], list_author[3]))
            else:
                self.string_list.append('|data-sort-value="{}"|[[{}|{}]]'
                                        .format(list_author[0], list_author[1], list_author[2]))
            self.string_list.append('|data-sort-value="{}"|{}'
                                    .format(list_author[5], list_author[4]))
            self.string_list.append('|data-sort-value="{}"|{}'
                                    .format(list_author[7], list_author[6]))
            self.string_list.append('|{}'.format(list_author[8]))
        self.string_list.append('|}')
        self.string_list.append('')
        self.string_list.append('== Anmerkungen ==')
        self.string_list.append('<references/>')
        self.string_list.append('')
        self.string_list.append('{{SORTIERUNG: Autoren  # Liste der}}')
        self.string_list.append('[[Kategorie:Listen]]')
        self.string_list.append('[[Kategorie:Autoren |!]]')

        return '\n'.join(self.string_list)

    def _handle_birth_and_death(self, event, author_dict):
        if author_dict[event] == '' or self.match_property.search(author_dict[event]):
            self.logger.debug('No valid entry in {} for {} ... Fallback to wikidata'.format(event, author_dict['title']))
            try:
                item = pywikibot.ItemPage(self.repo, author_dict['wikidata'])
                if event == 'birth':
                    property_label = 'P569'
                else:
                    property_label = 'P570'
                claim = item.text['claims'][property_label][0]
                date_from_data = claim.getTarget()
                if date_from_data.precision < 9:
                    self.logger.error('Precison is to low for {}'.format(author_dict['title']))
                    raise
                #elif date_from_data.precision < 8:
                #    if date_from_data.year < 1000:
                #        date_from_data = str(date_from_data.year)[0:1] + '. Jh.'
                #    else:
                #        date_from_data = str(date_from_data.year)[0:2] + '. Jh.'
                elif date_from_data.precision < 10:
                    date_from_data = str(date_from_data.year)
                elif date_from_data.precision < 11:
                    date_from_data = self.number_to_month[date_from_data.month] + ' ' + str(date_from_data.year)
                else:
                    date_from_data = str(date_from_data.day) + '. ' + self.number_to_month[date_from_data.month] + ' ' + str(date_from_data.year)
                if re.search('-', date_from_data):
                    date_from_data = date_from_data.replace('-', '') + ' v. Chr.'
                self.logger.debug('Found {} @ wikidata for {}'.format(date_from_data, event))
                return(date_from_data)  # 4,6
            except:
                self.logger.debug("Wasn't able to ge any data from wikidata")
                return('')  # 4,6
        else:
            return(author_dict[event])  # 4,6

if __name__ == "__main__":
    with open('../password.pwd') as password_file:
        password = load_password(password_file)
        wiki = pywikibot.Site(code= 'de', fam= 'wikisource', user='THEbotIT')
        login = LoginManager(site=wiki, password=password)
        login.login()

    bot = AuthorList(wiki)
    with SaveExecution(bot):
        bot.run()
