__author__ = 'erik'

import sys
sys.path.append('../../')
from tools.catscan import CatScan
from tools.date_conversion import DateConversion
from tools.template_handler import TemplateHandler
import os
import pywikibot
import json
import re


class AuthorList:
    def __init__(self, age):
        self.last_run = age

    def run(self):
        # debug or not
        debug = True

        searcher = CatScan()
        # is there pre rawdata?
        if os.path.isfile('data/raw_data.json') is True:
            # loading existing database
            with open('data/raw_data.json', 'r') as raw_data_file:
                database = json.load(raw_data_file)
            searcher.max_age(self.last_run + 1)  #all changes from age + 1 hour
        else:  #creating database
            database = {}
            searcher.set_timeout(120)

        searcher.add_namespace(0)  # search in main namespace
        searcher.add_positive_category('Autoren')
        searcher.add_yes_template('Personendaten')
        if debug:
            with open('data/result.json', 'r') as result_file:
                result = json.load(result_file)
        else:
            result = searcher.run()
        site = pywikibot.Site()
        for author in result:
            author = author['a']
            if debug:
                print(author['title'])
            #delete preexisting data of this author
            try:
                database.pop(author['id'])
            except:
                pass

            dict_author = {'title': author['title']}
            if debug:
                print(dict_author)

            #extract the Personendaten-block form the wikisource page
            page = pywikibot.Page(site, author['title'])
            personendaten = re.search('\{\{Personendaten(?:.|\n)*?\n\}\}\n', page.text).group()
            template_extractor = TemplateHandler(personendaten)
            dict_author.update({'name': template_extractor.get_parameter('NACHNAME')['value']})
            dict_author.update({'first_name': template_extractor.get_parameter('VORNAMEN')['value']})
            dict_author.update({'birth': template_extractor.get_parameter('GEBURTSDATUM')['value']})
            dict_author.update({'death': template_extractor.get_parameter('STERBEDATUM')['value']})
            dict_author.update({'description': template_extractor.get_parameter('KURZBESCHREIBUNG')['value']})
            dict_author.update({'synonyms': template_extractor.get_parameter('ALTERNATIVNAMEN')['value']})

            database.update({author['id']: dict_author})
        with open('data/raw_data.json', 'w') as raw_data_file:
            json.dump(database, raw_data_file, indent=4, sort_keys=True)


if __name__ == "__main__":
    run = AuthorList(1000000)
    run.run()
