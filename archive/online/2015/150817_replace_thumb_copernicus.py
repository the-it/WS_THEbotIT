# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
from tools.petscan import PetScan
import re
import requests
import pywikibot

searcher_catscan = PetScan()
searcher_catscan.add_positive_category('Nicolaus Coppernicus aus Thorn über die Kreisbewegungen der Weltkörper')
searcher_catscan.add_namespace('Seite')
sites = searcher_catscan.run()
site = pywikibot.Site()

for lemma in sites:
    page = pywikibot.Page(site, lemma['a']['nstext'] + ':' + lemma['a']['title'])
    test_for_fit = re.search('150px', page.text)
    print(lemma['a']['title'])
    if test_for_fit:
        print('do replacement')
        page.text = re.sub('150px', '300px', page.text)
        page.save(summary='bot edit: replace 150px with 300px', botflag=True, )