# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
import re
import pywikibot
from pywikibot import proofreadpage

def convert_RE_siehe(hit):
    print("1.{}".format(hit.group(1)))
    print("2.{}".format(hit.group(2)))
    if hit.group(1):
        temp =  "[[RE:" + hit.group(1) + "|" + hit.group(2) + "]]"
    else:
        temp =  "[[RE:" + hit.group(2) + "|" + hit.group(2) + "]]"
    print(temp)
    return temp

site = pywikibot.Site()

fit = re.compile("\{\{RE siehe\|?([^\}\|]*)\|([^\}\|]*)\}\}")

page = pywikibot.Page(site, 'RE:Register (Band XI)')
#statuspage = proofreadpage.ProofreadPage(site, 'Seite:LA2-Blitz-{}.jpg'.format(add_zeros(i, 4)))
fit1 = fit.search(page.text)
if fit1:
    tempText = fit.sub(lambda x: convert_RE_siehe(x), page.text)
    page.text = tempText
    #print(tempText)
    page.save(summary='RE siehe ersetzt durch [[]]', botflag=True, )