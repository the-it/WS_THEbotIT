
# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
from tools.catscan.catscan import CatScan
import re
import requests
import pywikibot
import copy
import roman

def build_arg(searcher):
    seite = int(searcher.group(1))
    if seite < 5:
        kapitel = '1'
    elif seite < 6:
        kapitel = '2'
    elif seite < 13:
        kapitel = '3'
    elif seite < 24:
        kapitel = '4'
    elif seite < 53:
        kapitel = '5'
    elif seite < 63:
        kapitel = '6'
    elif seite < 69:
        kapitel = '7'
    elif seite < 73:
        kapitel = '7.1'
    elif seite < 79:
        kapitel = '7.2'
    elif seite < 84:
        kapitel = '7.3'
    elif seite < 92:
        kapitel = '7.4'
    elif seite < 98:
        kapitel = '7.5'
    elif seite < 109:
        kapitel = '7.6'
    elif seite < 119:
        kapitel = '7.7'
    elif seite < 121:
        kapitel = '7.8'
    elif seite < 129:
        kapitel = '7.9'
    elif seite < 139:
        kapitel = '7.10'
    elif seite < 141:
        kapitel = '7.11'
    elif seite < 144:
        kapitel = '7.12'
    elif seite < 146:
        kapitel = '7.13'
    elif seite < 149:
        kapitel = '7.14'
    elif seite < 157:
        kapitel = '7.15'
    elif seite < 161:
        kapitel = '7.16'
    elif seite < 173:
        kapitel = '7.17'
    elif seite < 188:
        kapitel = '7.18'
    elif seite < 192:
        kapitel = '7.19'
    elif seite < 195:
        kapitel = '7.20'
    elif seite < 198:
        kapitel = '7.21'
    elif seite < 205:
        kapitel = '7.22'
    elif seite < 216:
        kapitel = '7.23'
    elif seite < 228:
        kapitel = '7.24'
    elif seite < 234:
        kapitel = '7.25'
    elif seite < 243:
        kapitel = '7.26'
    elif seite < 249:
        kapitel = '7.27'
    elif seite < 257:
        kapitel = '7.28'
    elif seite < 275:
        kapitel = '7.29'
    elif seite < 278:
        kapitel = '7.30'
    elif seite < 289:
        kapitel = '7.31'
    elif seite < 312:
        kapitel = '7.32'
    elif seite < 328:
        kapitel = '7.33'
    elif seite < 335:
        kapitel = '7.34'
    elif seite < 349:
        kapitel = '7.35'
    elif seite < 364:
        kapitel = '7.36'
    elif seite < 370:
        kapitel = '8'
    elif seite < 371:
        kapitel = '9'
    elif seite < 393:
        kapitel = '9.I'
    elif seite < 483:
        kapitel = '9.II'
    elif seite < 510:
        kapitel = '10'
    else:
        kapitel = '11'

    return '[[David Hilbert Gesammelte Abhandlungen Erster Band – Zahlentheorie/Kapitel ' + kapitel +'#' + searcher.group(1) + '|' + searcher.group(1) + ']]' + searcher.group(2)

wiki = pywikibot.Site()

regex = r'''(\d{1,3})([.,])'''

fit = re.compile(regex, re.VERBOSE)


page = pywikibot.Page(wiki, 'Seite:David Hilbert Gesammelte Abhandlungen Bd 1.djvu/553')
temp = fit.sub(lambda x: build_arg(x), page.text)
page.text = temp
test1 = 3
page.save(summary = 'setzen der Links auf die Seiten', botflag = True, async= True)