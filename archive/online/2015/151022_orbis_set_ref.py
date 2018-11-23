
# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
from tools.petscan.catscan import CatScan
import re
import requests
import pywikibot
import copy
import roman

wiki = pywikibot.Site()

regex = r'''\[\[Kategorie:Orbis sensualium pictus\]\]'''

cat_sort = CatScan()
cat_sort.add_positive_category("Seiten mit Referenzierungsfehlern")
cat_sort.add_positive_category("Orbis sensualium pictus")

for i in cat_sort.run():
    print(i['a']['title'])
    lemma = pywikibot.Page(wiki, i['a']['title'])
    new_text = re.sub(regex, '{{References|TIT|WS}}\n\n[[Kategorie:Orbis sensualium pictus]]', lemma.text)
    lemma.text = new_text
    lemma.save(summary= 'automatic add WS-Referenzes', botflag= True)