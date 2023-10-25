# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
from tools.petscan import PetScan
import re
import requests
import pywikibot

site = pywikibot.Site()

for i in range(260, 467):#467
    page = pywikibot.Page(site, 'Seite:Loos Sämtliche Schriften.pdf/' + str(i))
    test = page.backlinks(namespaces=0)
    #print(next(test))
    try:
        print(page.title())
        test2 = next(test).title()
        is_there_match = re.search('\{\{Seitenstatus2\|\[\[Adolf Loos\]\]\|\[\[Adolf Loos – Sämtliche Schriften\]\]\|Adolf Loos [-–] Sämtliche Schriften\|\}\}', page.text)
        if is_there_match:
            new_text = re.sub('\{\{Seitenstatus2\|\[\[Adolf Loos\]\]\|\[\[Adolf Loos – Sämtliche Schriften\]\]\|Adolf Loos [-–] Sämtliche Schriften\|\}\}',
                              '{{Seitenstatus2|[[Adolf Loos]]|[[Adolf Loos – Sämtliche Schriften]]|Adolf Loos - Sämtliche Schriften|[[%s]]}}' % test2,
                              page.text)
            print('{{Seitenstatus2|[[Adolf Loos]]|[[Adolf Loos – Sämtliche Schriften]]|Adolf Loos - Sämtliche Schriften|[[%s]]}}' % test2)
            page.text = new_text
            page.save(summary='Kapitel eingefügt', botflag=True)
    except:
        pass