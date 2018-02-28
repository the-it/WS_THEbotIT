# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
from tools.catscan import PetScan
import re
import requests
import pywikibot

site = pywikibot.Site()

for i in range(1, 467):
    page = pywikibot.Page(site, 'Seite:Loos Sämtliche Schriften.pdf/' + str(i))
    test_for_fit = re.search('Adolf Loos\]\]\|Adolf Loos [-–] Sämtliche Schriften', page.text)
    if test_for_fit:
        print(i)
        page.text = re.sub('Adolf Loos\]\]\|Adolf Loos [-–] Sämtliche Schriften', 'Adolf Loos]]|[[Adolf Loos – Sämtliche Schriften]]', page.text)
        page.save(summary='bot edit: set a link to the linking mainlemma', botflag=True, )