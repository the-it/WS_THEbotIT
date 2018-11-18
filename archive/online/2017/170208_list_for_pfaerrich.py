# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
import re
from pywikibot import Page, Site
from tools.catscan import PetScan

wiki = Site()

searcher = PetScan()
searcher.add_positive_category("RE:Korrigiert")
lemma_list = searcher.run()

list_for_pfaerrich = []
for idx_lem, lemma in enumerate(lemma_list):
    print(idx_lem)
    page = Page(wiki, lemma['title'])
    version_history = page.fullVersionHistory()[::-1]
    size_all_changes = 0
    for idx_rev, revision in enumerate(version_history):
        user = revision.user
        if user == 'Pfaerrich':
             if idx_rev > 0:
                 size_prev = len(version_history[idx_rev-1].text)
             else:
                 size_prev = 0
             size_all_changes += abs(len(version_history[idx_rev].text) - size_prev)
    korrigiert_flag = False
    if size_all_changes > 0:
        for version in page.getVersionHistory():
            if version.user == 'Pfaerrich':
                if re.search('orrigiert', version.comment):
                    korrigiert_flag = True
                    break
    print(size_all_changes, len(page.text), korrigiert_flag)
    if (size_all_changes / len(page.text)) < 0.03 and not korrigiert_flag:
        list_for_pfaerrich.append([page.title(), size_all_changes, len(page.text)])

report_page = Page(wiki, 'Benutzer:THEbotIT/List_for_Pfaerrich')

header = '{|class="wikitable sortable"\n! Lemma\n! Größe\n! geändert von dir'
text = []
for line in list_for_pfaerrich:
    text.append('|-\n|[[{lemma}]]\n|{size}\n|{changes}'.format(lemma=line[0], size=line[2], changes=line[1]))
text = '\n'.join(text)
text = '{header}\n{text}\n|}}'.format(header=header, text=text)
report_page.text = text
report_page.save(botflag=True, summary='blub')