# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
import re
import pywikibot

def convert_table(hit):
    return '\n|- \n|style="width: 20%"| {}\n|style="width: 60%"| {}\n|style="width: 20%; text-align:right;"| {}'.format(hit.group(1), hit.group(2), hit.group(3))

wiki = pywikibot.Site()

regex = re.compile("\n([^\s]*)\s*([^\s].*\.)\s*([\d]{1,3})")

for i in range(313, 320):
    print(i)
    page = pywikibot.Page(wiki, 'Seite:OrbisPictus {}.jpg'.format(i))
    temp_text = page.text
    page.text = regex.sub(lambda x: convert_table(x), temp_text)
    print(page.text)
    page.save()
