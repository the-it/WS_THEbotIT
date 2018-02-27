# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
import re
import pywikibot
from pywikibot import proofreadpage

def add_zeros(number, digits):
    number_str = str(number)
    if number < 10:
        for members in range(digits-1):
            number_str = "0" + number_str
    elif number < 100:
        for members in range(digits-2):
            number_str = "0" + number_str
    elif number < 1000:
        for members in range(digits-3):
            number_str = "0" + number_str
    return number_str

site = pywikibot.Site()

fit_datei = re.compile("\[\[Category:Meyers Blitz-Lexikon\]\]")

for i in range(1, 442):
    page = pywikibot.Page(site, 'Datei:LA2-Blitz-{}.jpg'.format(add_zeros(i, 4)))
    #statuspage = proofreadpage.ProofreadPage(site, 'Seite:LA2-Blitz-{}.jpg'.format(add_zeros(i, 4)))
    print(i)
    fit1 = fit_datei.search(page.text)
    if fit1:
        tempText = fit_datei.sub("[[Kategorie:Meyers Blitz-Lexikon/Seiten]]", page.text)
        page.text = tempText
        #print(tempText)
        page.save(summary='bot edit: Scans der Seiten automatisch in eigene Kategorie verschieben.', botflag=True, )