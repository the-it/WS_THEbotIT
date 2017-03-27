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

for i in range(34, 651):
    try:
        with open('dump/' + str(add_zeros(i, 3)) +'.txt' ) as file_pointer:
            content = file_pointer.read()
        print(i)
        page = pywikibot.Page(site, 'Seite:Wackernagel Geschichte der Stadt Basel Band 2,1.pdf/' + str(i))

        starter = '<noinclude><pagequality level="1" user="THEbotIT" /><div class="pagetext">{{Seitenstatus2|[[Rudolf Wackernagel]]|[[Geschichte der Stadt Basel. Zweiten Bandes erster Teil]]|Wackernagel Geschichte der Stadt Basel|}}\n\n\n</noinclude>'

        finisher = "<noinclude>{{Zitierempfehlung|Projekt=[[Rudolf Wackernagel]]: ''[[Geschichte der Stadt Basel. Zweiten Bandes erster Teil]]''. Helbing & Lichtenhahn, Basel 1911|Seite=%s}}</div></noinclude>\n" % (i-21)

        page.text = starter + content + finisher
        page.save(summary= 'automatische Seitenerstellung, bzw. Korrektur der Zitierempfehlung', botflag= True)
    except:
        pass
