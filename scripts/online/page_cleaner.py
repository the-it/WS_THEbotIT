# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
# pylint: disable=wrong-import-position
import pywikibot

SITE = pywikibot.Site('de', 'wikisource')
for i in range(1, 11):
    page = pywikibot.Page(SITE, 'Benutzer:THEbotIT/Test' + str(i))
    page.text = ""
    page.save(summary="clean the page", botflag=True)
