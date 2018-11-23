# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
import re
import requests
import pywikibot
from pywikibot import proofreadpage
from tools.petscan.catscan import CatScan

scanner = CatScan()
scanner.add_positive_category("Das Newe Testament Deutzsch (Septembertestament)")
scanner.add_positive_category("Unkorrigiert")
scanner.add_no_template("NotizLinks")
scanner.add_no_template("NotizRechts")
scanner.add_namespace("Seite")
lemmas = scanner.run()
site = pywikibot.Site()

for idx, lemma in enumerate(lemmas):

    page = proofreadpage.ProofreadPage(site, lemma["page_title"])
    page.user = 'THEbotIT'
    page.proofread()

    page.save(summary= "Randnotizen korrigiert (keine Randnotizen vorhanden)", botflag= True)