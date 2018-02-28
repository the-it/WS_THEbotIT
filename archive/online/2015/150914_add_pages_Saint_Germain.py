# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
from tools.catscan import PetScan
import re
import requests
import pywikibot

list_of_pages =[1134,
                1135,
                1136,
                1137,
                1138,
                1139,
                1140,
                1141,
                1142,
                1143,
                1144,
                1145,
                1146,
                1147,
                1148,
                1149,
                1150,
                1151,
                1152,
                1153,
                1154,
                1155,
                1156,
                1157,
                1158,
                1159,
                1160,
                1161,
                1162,
                1163,
                1164,
                1165,
                1166,
                1167,
                1168,
                1169,
                1170,
                1171,
                1172,
                1173,
                1174,
                1175,
                1176,
                1177,
                1178,
                1179,
                1180,
                1181,
                1182,
                1183,
                1184,
                1185,
                1186,
                1187,
                1188,
                1189,
                1190,
                1191,
                1192,
                1191,
                1194,
                1195,
                1196,
                1197,
                1198,
                1199,
                1200,
                1201,
                1203,
                1205,
                1207,
                1209,
                1211,
                1213,
                1215,
                1217,
                1219,
                1221,
                1223,
                1225,
                1227,
                1229,
                1231,
                1233,
                1234,
                1235,
                1236,
                1237,
                1238,
                1239,
                1240,
                1241,
                1243,
                1244]

header = '''<noinclude><pagequality level="1" user="THEbotIT" /><div class="pagetext">{{Seitenstatus2||[[Staatsvertrag von Saint-Germain-en-Laye]]. In: Staatsgesetzblatt für die Republik Österreich. Jahrgang 1920, S. 995–1244|Staatsvertrag von Saint-Germain-en-Laye|}}{{BlockSatzStart}}


</noinclude>'''

footer = '''<noinclude>{{BlockSatzEnd}}{{Zitierempfehlung|Projekt=: ''[[Staatsvertrag von Saint-Germain-en-Laye]]. In: Staatsgesetzblatt für die Republik Österreich. Jahrgang 1920, S. 995–1244''. Österreichische Staatsdruckerei, Wien 1920|Seite=%s}}</div></noinclude>'''

with open('saintgermain.txt', mode='r', encoding='utf8') as rawfile:
    text = re.split('\{\{Seite\|\d{3,4}\|\|Staatsgesetzblatt_\(Austria\)_1920_\d{4}\.jpg\}\}', rawfile.read())

site = pywikibot.Site()

for idx, i in enumerate(list_of_pages):
    if i == 995:
        continue
    if i < 1000:
        lemma = 'Seite:Staatsgesetzblatt (Austria) 1920 0{}.jpg'.format(i)
    else:
        lemma = 'Seite:Staatsgesetzblatt (Austria) 1920 {}.jpg'.format(i)

    page = pywikibot.Page(site, lemma)
    page.text = header + text[idx] + (footer % i)
    page.save(summary='Automatische Konvertierung von PR1 zu PR2', botflag=True)