# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
import re
import requests
import pywikibot
from pywikibot import proofreadpage

site = pywikibot.Site()

for i in range(1, 128):
    page = pywikibot.proofreadpage.ProofreadPage(site, 'Seite:Versuch über die wahre Art das Clavier zu spielen Teil 1 1759.pdf/{}'.format(i))
    print(page.status)
    page._full_header.user = 'THEbotIT'
    try:
        page.validate()
        page.save()
    except:
        pass
