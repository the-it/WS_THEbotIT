# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
import re
import pywikibot

wiki = pywikibot.Site()

for i in range(210,321):
    if i < 10:
        page = pywikibot.Page(wiki, 'Seite:OrbisPictus 00' + str(i) + '.jpg')
    elif i < 100:
        page = pywikibot.Page(wiki, 'Seite:OrbisPictus 0' + str(i) + '.jpg')
    else:
        page = pywikibot.Page(wiki, 'Seite:OrbisPictus ' + str(i) + '.jpg')

    temp = page.text

    temp = re.sub('width: 400"', 'width: 400px"', page.text)
    page.text = temp

    page.save(summary='400 -> 400px', botflag=True)


