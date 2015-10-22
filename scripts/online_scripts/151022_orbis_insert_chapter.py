# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
from tools.catscan import CatScan
import re
import requests
import pywikibot

#Skript doesn't work at the moment. It seems, that the database is lacking behind. Let's wait for a few days.
#Mazbe then all backlinks will be found.

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

for i in range(6, 308):#467
    page = pywikibot.Page(site, 'Seite:OrbisPictus {}.jpg'.format(add_zeros(i, 3)))
    print(page.title())
    test = page.backlinks(namespaces=0)
    #print(next(test))
    try:
        test2 = next(test).title()
        is_there_match = re.search('\{\{Seitenstatus2\|\[\[Johann Amos Comenius\]\]\|\[\[Orbis sensualium pictus\]\]\|Orbis sensualium pictus\|\}\}', page.text)
        if is_there_match:
            new_text = re.sub('\{\{Seitenstatus2\|\[\[Johann Amos Comenius\]\]\|\[\[Orbis sensualium pictus\]\]\|Orbis sensualium pictus\|\}\}',
                              '{{Seitenstatus2|[[Johann Amos Comenius]]|[[Orbis sensualium pictus]]|Orbis sensualium pictus|[[%s]]}}' % test2,
                              page.text)
            print('{{Seitenstatus2|[[Johann Amos Comenius]]|[[Orbis sensualium pictus]]|Orbis sensualium pictus|[[%s]]}}' % test2)
            page.text = new_text
            page.save(summary='Kapitel eingefügt', botflag=True)
    except:
        pass