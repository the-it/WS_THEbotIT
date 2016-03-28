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

for i in range(45, 673):
    try:
        with open('dump/raw_wacker/' + str(add_zeros(i, 3)) +'.txt' ) as file_pointer:
            content = file_pointer.read()
        print(i)
        page = pywikibot.Page(site, 'Seite:Wackernagel Geschichte der Stadt Basel Band 1.pdf/' + str(i))

        starter = '<noinclude><pagequality level="1" user="THEbotIT" /><div class="pagetext">{{Seitenstatus2|[[Rudolf Wackernagel]]|[[Geschichte der Stadt Basel. Erster Band]]|Wackernagel Geschichte der Stadt Basel|}}{{BlockSatzStart}}\n\n\n</noinclude>'

        finisher = "<noinclude>{{BlockSatzEnd}}{{Zitierempfehlung|Projekt=[[Rudolf Wackernagel]]: ''[[Geschichte der Stadt Basel. Erster Band]]''. Helbing & Lichtenhahn, Basel 1907|Seite=%s}}</div></noinclude>\n" % (i-19)

        page.text = starter + content + finisher
        page.save(summary= 'automatische Seitenerstellung', botflag= True)
    except:
        pass
