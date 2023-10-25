# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
import re
import pywikibot
from pywikibot import proofreadpage
from tools.petscan.catscan import CatScan

searcher_index = CatScan()
searcher_index.add_namespace(0)
searcher_index.add_positive_category('Fertig')
searcher_index.add_positive_category('Korrigiert')
searcher_index.add_positive_category('Unkorrigiert')
searcher_index.add_positive_category('Unvollständig')
searcher_index.add_positive_category('Fertig')
searcher_index.set_logic_union()
searcher_index.set_timeout(240)
searcher_index.set_regex_filter('David Hilbert.*')

lemmas = searcher_index.run()

wiki = pywikibot.Site()

regex_cat = re.compile("\[\[Kategorie:David Hilbert Gesammelte Abhandlungen Erster Band\]\]")
regex_block_start = re.compile("\{\{BlockSatzStart\}\}")
regex_block_end = re.compile("\{\{BlockSatzEnd\}\}")

for i, lemma in enumerate(lemmas):
    print(i, "/", len(lemmas), lemma)
    page = pywikibot.Page(wiki, lemma['page_title'])
    temp_text = page.text
    if regex_cat.search(temp_text):
        temp_text = regex_cat.sub('[[Kategorie:David Hilbert Gesammelte Abhandlungen Erster Band|!]]', temp_text)
        page.text = temp_text
        page.save(summary='Format überarbeitet', botflag=True)

