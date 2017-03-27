# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
import re
import pywikibot

def convert_vor(hit, number):
    return '|VORGÄNGER=Archias {}'.format(i-1)

def convert_nach(hit, number):
    return '|NACHFOLGER=Archias {}'.format(i+1)

wiki = pywikibot.Site()

regex_vor = re.compile("\|VORGÄNGER=")
regex_nach = re.compile("\|NACHFOLGER=")

for i in range(67, 113):
    print(i)
    page = pywikibot.Page(wiki, 're:Archias {}'.format(i))
    temp_text = page.text
    temp_text = regex_vor.sub(lambda x: convert_vor(x, i), temp_text)
    page.text = regex_nach.sub(lambda x: convert_nach(x, i), temp_text)
    print(page.text)
    page.save('Fehlende Parameter ergänzt', botflag=True)
