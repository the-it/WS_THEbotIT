# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
from tools.catscan import CatScan
import re
import requests
import pywikibot
from pywikibot import proofreadpage

site = pywikibot.Site()

for i in range(455, 474):
    page = pywikibot.proofreadpage.ProofreadPage(site, 'Seite:Riessler Altjuedisches Schrifttum ausserhalb der Bibel {}.jpg'.format(i))
    print(page.status)
    page._full_header.user = 'THEbotIT'
    page.proofread()
    page.save()
