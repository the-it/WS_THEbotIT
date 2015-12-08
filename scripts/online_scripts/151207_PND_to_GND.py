# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
from tools.catscan.catscan import CatScan
import re
import pywikibot

wiki = pywikibot.Site()

searcher = CatScan()
searcher.add_yes_template("ADBDaten")
searcher.set_timeout(120)
lemmas = searcher.run()
gesamt = len(lemmas)
seite = 1

for lemma in lemmas:
    page = pywikibot.Page(wiki, lemma['a']['title'])
    print("Seite {}/{}".format(seite, gesamt))
    seite += 1
    try:
        is_there_match = re.search('\|PND', page.text)
        if is_there_match:
            new_text = re.sub('\|PND', '|GND', page.text)
            page.text = new_text
            print(page.title())
            page.save(summary='Vorlage_ADBDaten: Parameter PND wurde zu GND umgewandelt.', botflag=True)
    except:
        pass