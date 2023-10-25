# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
import re
import pywikibot

site = pywikibot.Site()

for i in range(277, 290):
    page = pywikibot.Page(site, 'Seite:Loos Sämtliche Schriften.pdf/' + str(i))
    page.text = re.sub('\[\[Adolf Loos – Sämtliche Schriften\]\]\|\|', '[[Adolf Loos – Sämtliche Schriften]]|Adolf Loos – Sämtliche Schriften|', page.text)
    page.save(summary='bot edit: add project cat', botflag=True, )