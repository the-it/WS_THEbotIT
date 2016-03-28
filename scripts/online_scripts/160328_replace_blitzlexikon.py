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

for i in range(1, 442):
    page = pywikibot.Page(site, 'Seite:LA2-Blitz-{}.jpg'.format(add_zeros(i, 4)))
    print(i)
    fit1 = re.search("»", page.text)
    fit2 = re.search("—", page.text)
    if fit1 or fit2:
        statuspage = proofreadpage.ProofreadPage(site, 'Seite:LA2-Blitz-{}.jpg'.format(add_zeros(i, 4)))
        tempText = re.sub('»', '„', page.text)
        tempText = re.sub('«', '“', tempText)
        if statuspage.status == "Unkorrigiert":
            tempText = re.sub('—', '\n\n', tempText)
        page.text = tempText
        #print(tempText)
        page.save(summary='bot edit: — -> Leerzeile, »« -> „“', botflag=True, )