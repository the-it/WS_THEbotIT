# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
from tools.catscan import PetScan
import re
import requests
import pywikibot

searcher_index = PetScan()
searcher_index.add_namespace('Index')
searcher_index.add_positive_category('Index')
list_of_indexes = searcher_index.run()
wiki = pywikibot.Site()

for idx, index in enumerate(list_of_indexes):
    print('{}/{} {}'.format(idx + 1, len(list_of_indexes), index['a']['title']))
    searcher_sites_of_index = PetScan()
    searcher_sites_of_index.add_namespace('Seite')
    searcher_sites_of_index.add_yes_outlink(index['a']['nstext'] + ':' + index['a']['title'])
    searcher_sites_of_index.add_positive_category('Fertig')
    searcher_sites_of_index.add_positive_category('Korrigiert')
    searcher_sites_of_index.add_positive_category('Unkorrigiert')
    searcher_sites_of_index.set_logic(log_or=True)
    list_of_sites = searcher_sites_of_index.run()
    for idx, site in enumerate(list_of_sites):
        print('\t{}/{} {}'.format(idx + 1, len(list_of_sites), site['a']['nstext'] + ':' + site['a']['title']))
        touchpage = pywikibot.Page(wiki, title =site['a']['nstext'] + ':' + site['a']['title'])
        touchpage.touch()
    del searcher_sites_of_index
