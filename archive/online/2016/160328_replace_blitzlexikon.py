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


def get_buchstabe(wort:str):
    if wort[0] == "S":
        if wort[1] < "c":
            return "S"
        elif wort[1] < "d":
            return "Sch"
        elif wort[1] < "h":
            return "Sd"
        elif wort[1] < "t":
            return "Sh"
        else:
            return "St"
    elif wort[0] == "I" or wort[0] == "J":
        return "I, J"
    else:
        return wort[0]


def convert_link(hit):
    wort = hit.group(1)
    try:
        point = hit.group(2)
    except:
        point = ""
    buchstabe = get_buchstabe(wort)
    fit1 = re.search("Tafel", wort)
    fit2 = re.search("Taf.", wort)
    fit3 = re.search("Abb.", wort)
    fit4 = re.search("Karte", wort)
    if fit1 or fit2 or fit3 or fit4:
        backdings = hit.group(0)
    else:
        backdings = "↑ [[Meyers Blitz-Lexikon/" + buchstabe + "#" + wort + "|" + wort + "]]"
    tester = backdings[-3]
    print(tester)
    if backdings[-3] == ".":
        backdings = backdings[:-3]
        backdings = backdings + "]]."
    if backdings[-3] == ",":
        backdings = backdings[:-3]
        backdings = backdings + "]],"
    print(backdings)
    return backdings

site = pywikibot.Site()

fit = re.compile("↑ ?\[\[Seite:LA2-Blitz-\d{4}\.jpg\|([^\]]*?)([\.,])?\]\]")

for i in range(1, 442):
    page = pywikibot.Page(site, 'Seite:LA2-Blitz-{}.jpg'.format(add_zeros(i, 4)))
    #statuspage = proofreadpage.ProofreadPage(site, 'Seite:LA2-Blitz-{}.jpg'.format(add_zeros(i, 4)))
    print(i)
    fit1 = fit.search(page.text)
    if fit1:
        tempText = fit.sub(lambda x: convert_link(x), page.text)
        page.text = tempText
        #print(tempText)
        page.save(summary='bot edit: vorhandene Links korrigiert', botflag=True, )