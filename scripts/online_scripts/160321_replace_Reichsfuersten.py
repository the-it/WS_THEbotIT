# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
import re
import pywikibot

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

def fett_sperr(hit):
    print("{{SperrSchrift|" + hit.group(0)[3:-3] + "}}")
    return "{{SperrSchrift|" + hit.group(0)[3:-3] + "}}"

site = pywikibot.Site()

fit = re.compile("'''[^']{1,200}'''")

for i in range(1, 425):
    page = pywikibot.Page(site, 'Seite:Ficker Vom Reichsfürstenstande {}.jpg'.format(add_zeros(i, 3)))
    print(i)
    fit1 = re.search("'''[^']{1,200}'''", page.text)
    fit2 = re.search("—", page.text)
    if fit1 or fit2:
        tempText = re.sub('—', '–', page.text)
        if i > 143:
            tempText = fit.sub(lambda x: fett_sperr(x), tempText)
        page.text = tempText
        #print(tempText)
        page.save(summary='bot edit: — -> –, Fettdruck -> SperrSchrift', botflag=True, )