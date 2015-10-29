
# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
from tools.catscan.catscan import CatScan
from tools.wiki_template_handler.template_handler import TemplateHandler
import re
import requests
import pywikibot
import copy
import roman

lemmas = ["Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Dritten Theils erste Abtheilung/Achtzehntes Buch",
"Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Dritten Theils erste Abtheilung/Dreyzehntes Buch",
"Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Dritten Theils erste Abtheilung/Funfzehntes Buch",
"Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Dritten Theils erste Abtheilung/Sechzehntes Buch",
"Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Dritten Theils erste Abtheilung/Siebzehntes Buch",
"Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Dritten Theils erste Abtheilung/Vierzehntes Buch",
"Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Dritten Theils zweyte Abtheilung/Ein und zwanzigstes Buch",
"Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Dritten Theils zweyte Abtheilung/Neunzehntes Buch",
"Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Dritten Theils zweyte Abtheilung/Zwanzigstes Buch",
"Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Dritten Theils zweyte Abtheilung/Zwey und zwanzigstes Buch",
"Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Erster Theil/Drittes Buch",
"Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Erster Theil/Erstes Buch",
"Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Erster Theil/Fünftes Buch",
"Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Erster Theil/Sechstes Buch",
"Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Erster Theil/Viertes Buch",
"Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Erster Theil/Zweytes Buch",
"Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Zweyter Theil/Achtes Buch",
"Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Zweyter Theil/Eilftes Buch",
"Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Zweyter Theil/Neuntes Buch",
"Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Zweyter Theil/Siebentes Buch",
"Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Zweyter Theil/Zehntes Buch",
"Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Zweyter Theil/Zwölftes Buch"]

wiki = pywikibot.Site()

wiki = pywikibot.Site()

lemma_dummy = 'Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Erster Theil/Zweytes Buch'
page = pywikibot.Page(wiki, title= 'Benutzer:THEbotIT/Test2')
template_textdaten = re.search('\{\{Textdaten(?:\{\{.*?\}\}|.)*?\}\}', page.text, re.DOTALL).group()
list_textdaten = TemplateHandler(template_textdaten).get_parameterlist()

template_navigation = TemplateHandler()
template_navigation.set_title('Kapitel')

list_navigation = []
list_navigation.append({'key': 'HERKUNFT', 'value': "Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung"})
list_navigation.append({'key': 'VORIGER', 'value': list_textdaten[0]['value']})
list_navigation.append({'key': 'NÄCHSTER', 'value': list_textdaten[1]['value']})
list_navigation.append({'key': 'TITELTEIL', 'value': '3'})
list_navigation.append({'key': 'BILD', 'value': list_textdaten[17]['value']})
list_navigation.append({'key': 'BEARBEITUNGSSTAND', 'value': 'fertig'})

template_navigation.update_parameters(list_navigation)

print(page.text)

page.text = re.sub('\{\{Textdaten(?:\{\{.*?\}\}|.)*?\}\}', template_navigation.get_str(), page.text)
print(template_navigation.get_str())

pass