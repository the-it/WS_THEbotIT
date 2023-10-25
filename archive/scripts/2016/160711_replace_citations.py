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

wiki = pywikibot.Site()

regex = re.compile("\{\{Zitierempfehlung\|Projekt=Karl Zeumer: ''Quellensammlung zur Geschichte der Deutschen Reichsverfassung in Mittelalter und Neuzeit''\.Tübingen: Verlag von J\.C\.B\. Mohr \(Paul Siebeck\), 1913\|Seite=(\d{1,3})\}\}")

for i in range(1, 563):
    print(i)
    page = pywikibot.Page(wiki, 'Seite:De Zeumer V2 {}.jpg'.format(add_zeros(i, 3)))
    temp_text = page.text
    if regex.search(temp_text):
        if int(regex.search(temp_text).group(1)) != i:
            temp_text = regex.sub("{{Zitierempfehlung|Projekt=Karl Zeumer: ''Quellensammlung zur Geschichte der Deutschen Reichsverfassung in Mittelalter und Neuzeit''.Tübingen: Verlag von J.C.B. Mohr (Paul Siebeck), 1913|Seite=" + str(i) +"}}", temp_text)
            page.text = temp_text
            page.save(summary='Zitierempfehlung korrigiert', botflag=True)

