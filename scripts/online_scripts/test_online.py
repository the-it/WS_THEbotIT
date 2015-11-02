# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
import pywikibot

site = pywikibot.Site('de', 'wikisource')
for i in range(11):
    page = pywikibot.Page(site, 'Benutzer:THEbotIT/Test' + str(i))
    page.text = ""
    page.save(summary="clean the page", botflag=True)