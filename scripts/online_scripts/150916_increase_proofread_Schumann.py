# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
import pywikibot
from pywikibot import proofreadpage

site = pywikibot.Site()

for i in range(50, 126):
    page = pywikibot.proofreadpage.ProofreadPage(site, 'Seite:Gesammelte Schriften über Musik und Musiker Bd.2 (1854).pdf/{}'.format(i))
    print(page.status)
    page._full_header.user = 'THEbotIT'
    page.proofread()
    page.save(summary="automatisch, IP hatte den Korrekturstand nicht hochgesetzt")
