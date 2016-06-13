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

    def __dig_up_data(self):
        self.timestamp = None

    def run(self):
        lemma_list = self.run_searcher()
        self.build_database(lemma_list)

    def run_searcher(self):
        # was the last run successful
        if self.last_run and self.last_run['succes'] and self.data:
            start_of_search = self.last_run['timestamp'] - timedelta(days=1)
            self.searcher.last_change_after(int(start_of_search.strftime('%Y')),
                                            int(start_of_search.strftime('%m')),
                                            int(start_of_search.strftime('%d')) )
            self.logger.info('The date {} is set to the argument "after".'.format(start_of_search.strftime("%d.%m.%Y")))
        elif __debug__:
            yesterday = datetime.datetime.now() - timedelta(days=1)
            self.searcher.last_change_after(int(yesterday.strftime('%Y')),
                                            int(yesterday.strftime('%m')),
                                            int(yesterday.strftime('%d')) )
        else:
            self.logger.warning('There was no timestamp found of the last run, so the argument "after" is not set.')
        self.searcher.add_namespace(0)  # search in main namespace
        self.searcher.add_positive_category('Autoren')
        self.searcher.add_yes_template('Personendaten')
        self.searcher.get_wikidata_items()

        print(self.searcher)

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
                personendaten = re.search('\{\{Personendaten(?:.|\n)*?\n\}\}\n', page.text).group()
                if personendaten:
                    template_extractor = TemplateHandler(personendaten)
                    dict_author.update({'name': template_extractor.get_parameter('NACHNAME')['value']})
                    dict_author.update({'first_name': template_extractor.get_parameter('VORNAMEN')['value']})
                    dict_author.update({'birth': template_extractor.get_parameter('GEBURTSDATUM')['value']})
                    dict_author.update({'death': template_extractor.get_parameter('STERBEDATUM')['value']})
                    dict_author.update({'description': template_extractor.get_parameter('KURZBESCHREIBUNG')['value']})
                    dict_author.update({'synonyms': template_extractor.get_parameter('ALTERNATIVNAMEN')['value']})
                    dict_author.update({'wikidata' : author['q']})
                else:
                    self.logger.error('No valid block "Personendaten" was found.')
            except Exception as e:
                self.logger.error(traceback.format_exc())
                self.logger.error('author {} have a problem'.format(author['title']))
            self.data.update({author['id']: dict_author})


if __name__ == "__main__":
    bot = AuthorList()
    with SaveExecution(bot):
        bot.run()
