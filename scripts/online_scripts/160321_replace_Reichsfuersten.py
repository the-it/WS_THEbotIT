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

def convert_template(hit):
    number = hit.group(1)
    return "{{NotizLinks|" + number + "|0|0|70}}{{Anker|" + number + "}}"


site = pywikibot.Site()

fit = re.compile("\{\{Randnotiz rechts\|(\d{1,3})\}\}")

for i in range(1, 425):
    page = pywikibot.Page(site, 'Seite:Ficker Vom Reichsfürstenstande {}.jpg'.format(add_zeros(i, 3)))
    print(i)
    fit1 = fit.search(page.text)
    if fit1:
        tempText = page.text
        tempText = fit.sub(lambda x: convert_template(x), tempText)
        page.text = tempText
        #print(tempText)
        page.save(summary='bot edit: Neuausrichtung der Randnotizen', botflag=True, )