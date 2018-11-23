# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
import re
import pywikibot
from tools.petscan import PetScan

wiki = pywikibot.Site()

regex_suez = re.compile("\[\[Der Canal von Suez\]\]")

searcher = PetScan()
searcher.add_positive_category('Der Canal von Suez')
lemmas = searcher.run()

for lemma in lemmas:
    print(lemma)
    page = pywikibot.Page(wiki, '{}:{}'.format(lemma['nstext'], lemma['title']))
    temp_text = page.text
    page.text = regex_suez.sub('[[Der Canal von Suez (Nordische Revue 1864)|Der Canal von Suez]]', temp_text)
    print(page.text)
    page.save('Link korrigiert', botflag=True)
