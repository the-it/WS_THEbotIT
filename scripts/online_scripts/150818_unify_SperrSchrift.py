# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
from tools.catscan import CatScan
import re
import requests
import pywikibot

searcher_catscan = CatScan()
searcher_catscan.add_namespace('Seite')
searcher_catscan.add_namespace(0)
searcher_catscan.add_yes_template('Sperrschrift')
sites = searcher_catscan.run()
site = pywikibot.Site()

for lemma in sites:
    if lemma['a']['nstext'] == '(Article)':
        page = pywikibot.Page(site, lemma['a']['title'])
    else:
        page = pywikibot.Page(site, lemma['a']['nstext'] + ':' + lemma['a']['title'])
    test_for_fit = re.search('Sperrschrift', page.text)
    #print(lemma['a']['title'])
    if test_for_fit:
        page.text = re.sub('Sperrschrift', 'SperrSchrift', page.text)
        page.save(summary='bot edit: Vereinheitlichung der Vorlage Sperrschrift zu SperrSchrift', botflag=True, )