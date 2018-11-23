# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
import re
import pywikibot
from tools.petscan import PetScan

wiki = pywikibot.Site()

table_of_chapters = {1: '1',
                     5: '2',
                     6: '3',
                     13: '4',
                     24: '5',
                     53: '6',
                     63: '7',
                     69: '7.1',
                     73: '7.2',
                     79: '7.3',
                     84: '7.4',
                     92: '7.5',
                     98: '7.6',
                     109: '7.7',
                     119: '7.8',
                     121: '7.9',
                     129: '7.10',
                     139: '7.11',
                     141: '7.12',
                     144: '7.13',
                     146: '7.14',
                     149: '7.15',
                     157: '7.16',
                     161: '7.17',
                     173: '7.18',
                     188: '7.19',
                     192: '7.20',
                     195: '7.21',
                     198: '7.22',
                     205: '7.23',
                     216: '7.24',
                     228: '7.25',
                     234: '7.26',
                     243: '7.27',
                     249: '7.28',
                     257: '7.29',
                     275: '7.30',
                     278: '7.31',
                     289: '7.32',
                     312: '7.33',
                     328: '7.34',
                     335: '7.35',
                     349: '7.36',
                     356: '7.Literatur',
                     362: '7.Verzeichnis der Sätze und Hilfssätze',
                     364: '8',
                     370: '9',
                     371: '9.I',
                     393: '9.II',
                     483: '10',
                     510: '11',
                     528: 'Anmerk. Hasse',
                     536: 'Verzeichnis'}

regex = re.compile("\[\[Der Canal von Suez\]\]")

for i in range(18,557):
    j = i-17
    print('###', i)
    for key in sorted(list(table_of_chapters.keys()),reverse=True):
        if j >= key:
            chapter = table_of_chapters[key]
            break
    print(table_of_chapters.keys())
    #temp_text = page.text
    #page.text = regex_suez.sub('[[Der Canal von Suez (Nordische Revue 1864)|Der Canal von Suez]]', temp_text)
    #print(page.text)
    #page.save('Link korrigiert', botflag=True)
