# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
import re
from pywikibot import Page, Site
from tools.catscan import PetScan

wiki = Site()

searcher = PetScan()
searcher.add_yes_template('Biel')
lemma_list = searcher.run()

for idx, lemma in enumerate(lemma_list):
    print(idx, len(lemma_list), lemma['title'])
    link_page = Page(wiki, lemma['title'])
    temp_text = link_page.text
    if re.search('\{\{Biel\|', temp_text):
        temp_text = re.sub('\{\{Biel\|1240647\}\}', '{{Bielefeld|1240647}}', temp_text)
        temp_text = re.sub('\{\{Biel\|590504\}\}', '{{Bielefeld|590504}}', temp_text)
        temp_text = re.sub('\{\{Biel\|1732676\}\}', '{{Bielefeld|1732676}}', temp_text)
        temp_text = re.sub('\{\{Biel\|548435\}\}', '{{Bielefeld|548435}}', temp_text)
        temp_text = re.sub('\{\{Biel\|32920\}\}', '{{Bielefeld|32920}}', temp_text)
    if link_page.text != temp_text:
        link_page.text = temp_text
        link_page.save(botflag=True, summary='Biel -> Bielefeld')

#report_page = Page(wiki, 'Benutzer:THEbotIT/List_for_Pfaerrich')

#header = '{|class="wikitable sortable"\n! Lemma\n! Größe\n! geändert von dir'
#text = []
#for line in list_for_pfaerrich:
#    text.append('|-\n|[[{lemma}]]\n|{size}\n|{changes}'.format(lemma=line[0], size=line[2], changes=line[1]))
#text = '\n'.join(text)
#text = '{header}\n{text}\n|}}'.format(header=header, text=text)
#report_page.text = text
#report_page.save(botflag=True, summary='blub')