# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
from tools.petscan.catscan import CatScan
import re
import requests
import pywikibot

searcher_index = CatScan()
searcher_index.add_namespace('Index')
searcher_index.add_positive_category('Index')
list_of_indexes = searcher_index.run()
wiki = pywikibot.Site()

for idx, index in enumerate(list_of_indexes):
    print('{}/{} {}'.format(idx + 1, len(list_of_indexes), index['a']['title']))
    touchpage = pywikibot.Page(wiki, title ="Index:"+index['a']['title'])
    touchpage.touch()
