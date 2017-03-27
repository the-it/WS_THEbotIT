# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
from tools.catscan import PetScan
from tools.template_handler import TemplateHandler
import re
import requests
import pywikibot
import copy


sites = ['Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Dritten Theils erste Abtheilung',
'Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Dritten Theils erste Abtheilung/Achtzehntes Buch',
'Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Dritten Theils erste Abtheilung/Dreyzehntes Buch',
'Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Dritten Theils erste Abtheilung/Funfzehntes Buch',
'Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Dritten Theils erste Abtheilung/Sechzehntes Buch',
'Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Dritten Theils erste Abtheilung/Siebzehntes Buch',
'Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Dritten Theils erste Abtheilung/Vierzehntes Buch',
'Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Dritten Theils zweyte Abtheilung',
'Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Dritten Theils zweyte Abtheilung/Ein und zwanzigstes Buch',
'Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Dritten Theils zweyte Abtheilung/Neunzehntes Buch',
'Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Dritten Theils zweyte Abtheilung/Zwanzigstes Buch',
'Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Dritten Theils zweyte Abtheilung/Zwey und zwanzigstes Buch',
'Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Erster Theil',
'Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Erster Theil/Drittes Buch',
'Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Erster Theil/Erstes Buch',
'Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Erster Theil/Fünftes Buch',''
'Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Erster Theil/Sechstes Buch',
'Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Erster Theil/Viertes Buch',
'Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Erster Theil/Zweytes Buch',
'Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Inhalt',
'Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Zweyter Theil',
'Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Zweyter Theil/Achtes Buch',
'Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Zweyter Theil/Eilftes Buch',
'Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Zweyter Theil/Neuntes Buch',
'Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Zweyter Theil/Siebentes Buch',
'Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Zweyter Theil/Zehntes Buch',
'Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Zweyter Theil/Zwölftes Buch']

wiki = pywikibot.Site()

lemma_dummy = 'Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Erster Theil/Erstes Buch'
page = pywikibot.Page(wiki, title= 'Benutzer:THEbotIT/Test2')
template_textdaten = re.search('\{\{Textdaten(?:\{\{.*?\}\}|.)*?\}\}', page.text, re.DOTALL).group()
list_textdaten = TemplateHandler(template_textdaten).get_parameterlist()

template_navigation1 = TemplateHandler()
template_navigation1.set_title('Navigation2')
template_navigation2 = TemplateHandler()
template_navigation2.set_title('Navigation2')

list_navigation = []
list_navigation.append({'key': 'AUTOR', 'value': '[[Basilius von Ramdohr]]'})
list_navigation.append({'key': 'ARTIKEL', 'value': '[[Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung|Venus Urania]]'})
list_navigation.append({'key': 'KAPITEL', 'value': list_textdaten[3]['value']})
list_navigation.append({'key': 'VORIGER', 'value': list_textdaten[0]['value']})
list_navigation.append({'key': 'NÄCHSTER', 'value': list_textdaten[1]['value']})
list_navigation.append({'key': 'STATUS', 'value': 'fertig'})

list_nav_reduce = copy.deepcopy(list_navigation)
list_nav_reduce.pop(0)
list_nav_reduce.pop(0)
list_nav_reduce.pop(0)
list_nav_reduce.pop(2)
list_nav_reduce.append({'key': 'TOP', 'value': 'x'})

template_navigation1.update_parameters(list_navigation)
template_navigation2.update_parameters(list_nav_reduce)

print(page.text)

page.text = re.sub('\{\{Textdaten(?:\{\{.*?\}\}|.)*?\}\}', template_navigation1.get_str(), page.text)
page.text = page.text + template_navigation2.get_str()

pass