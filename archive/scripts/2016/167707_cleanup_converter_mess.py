# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
import re
from pywikibot import Page, Site
from pywikibot.pagegenerators import SearchPageGenerator

wiki = Site()

generator = SearchPageGenerator('insource: "Kategorie:re:Verweisung"', namespaces=[0])

regex = re.compile('[^\[]Kategorie:re:Verweisung')

for idx, lemma in enumerate(generator):
    print(idx)
    if regex.search(lemma.text):
        lemma.text = re.sub('Kategorie:re:Verweisung', '[[Kategorie:re:Verweisung', lemma.text)
        lemma.save('REScanner: Bugfix, Link entfernt')

