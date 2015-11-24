
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

lemmas = ["Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/Erster Theil/Fünftes Buch",
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

for lemma in lemmas:
    page = pywikibot.Page(wiki, title= lemma)
    template_textdaten = re.search('\{\{Textdaten(?:\{\{.*?\}\}|.)*?\}\}', page.text, re.DOTALL).group()
    template_handler_orig = TemplateHandler(template_textdaten)

    template_navigation = TemplateHandler()
    template_navigation.set_title('Kapitel')

    list_navigation = []
    list_navigation.append({'key': 'HERKUNFT', 'value': "Venus Urania. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung"})
    list_navigation.append({'key': 'VORIGER', 'value': re.sub('Venus Urania\. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/', '', template_handler_orig.get_parameter('VORIGER')['value'])})
    list_navigation.append({'key': 'NÄCHSTER', 'value': re.sub('Venus Urania\. Ueber die Natur der Liebe, über ihre Veredelung und Verschönerung/', '', template_handler_orig.get_parameter('NÄCHSTER')['value'])})
    list_navigation.append({'key': 'TITELTEIL', 'value': '3'})
    list_navigation.append({'key': 'BILD', 'value': template_handler_orig.get_parameter('BILD')['value']})
    list_navigation.append({'key': 'BEARBEITUNGSSTAND', 'value': 'fertig'})
    list_navigation.append({'key': 'KATEGORIE', 'value': 'Venus Urania'})

    template_navigation.update_parameters(list_navigation)

    page.text = re.sub('\{\{Textdaten(?:.|\n)*?\n\}\}', template_navigation.get_str(), page.text)
    page.save(summary= 'Umstellung auf Vorlage Kapitel', botflag= True)
