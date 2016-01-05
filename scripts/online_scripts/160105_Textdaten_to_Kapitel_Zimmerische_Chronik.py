# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
from tools.wiki_template_handler.template_handler import TemplateHandler
import re
import pywikibot


lemmas = ["Zimmerische Chronik Band 1:Kapitel 10",
"Zimmerische Chronik Band 1:Kapitel 11",
"Zimmerische Chronik Band 1:Kapitel 12",
"Zimmerische Chronik Band 1:Kapitel 13",
"Zimmerische Chronik Band 1:Kapitel 14",
"Zimmerische Chronik Band 1:Kapitel 15",
"Zimmerische Chronik Band 1:Kapitel 16",
"Zimmerische Chronik Band 1:Kapitel 17",
"Zimmerische Chronik Band 1:Kapitel 18",
"Zimmerische Chronik Band 1:Kapitel 19",
"Zimmerische Chronik Band 1:Kapitel 2",
"Zimmerische Chronik Band 1:Kapitel 20",
"Zimmerische Chronik Band 1:Kapitel 21",
"Zimmerische Chronik Band 1:Kapitel 22",
"Zimmerische Chronik Band 1:Kapitel 23",
"Zimmerische Chronik Band 1:Kapitel 24",
"Zimmerische Chronik Band 1:Kapitel 25",
"Zimmerische Chronik Band 1:Kapitel 26",
"Zimmerische Chronik Band 1:Kapitel 27",
"Zimmerische Chronik Band 1:Kapitel 28",
"Zimmerische Chronik Band 1:Kapitel 29",
"Zimmerische Chronik Band 1:Kapitel 3",
"Zimmerische Chronik Band 1:Kapitel 30",
"Zimmerische Chronik Band 1:Kapitel 31",
"Zimmerische Chronik Band 1:Kapitel 32",
"Zimmerische Chronik Band 1:Kapitel 33",
"Zimmerische Chronik Band 1:Kapitel 34",
"Zimmerische Chronik Band 1:Kapitel 35",
"Zimmerische Chronik Band 1:Kapitel 36",
"Zimmerische Chronik Band 1:Kapitel 37",
"Zimmerische Chronik Band 1:Kapitel 38",
"Zimmerische Chronik Band 1:Kapitel 39",
"Zimmerische Chronik Band 1:Kapitel 4",
"Zimmerische Chronik Band 1:Kapitel 40",
"Zimmerische Chronik Band 1:Kapitel 41",
"Zimmerische Chronik Band 1:Kapitel 42",
"Zimmerische Chronik Band 1:Kapitel 43",
"Zimmerische Chronik Band 1:Kapitel 44",
"Zimmerische Chronik Band 1:Kapitel 45",
"Zimmerische Chronik Band 1:Kapitel 46",
"Zimmerische Chronik Band 1:Kapitel 47",
"Zimmerische Chronik Band 1:Kapitel 48",
"Zimmerische Chronik Band 1:Kapitel 49",
"Zimmerische Chronik Band 1:Kapitel 5",
"Zimmerische Chronik Band 1:Kapitel 50",
"Zimmerische Chronik Band 1:Kapitel 51",
"Zimmerische Chronik Band 1:Kapitel 52",
"Zimmerische Chronik Band 1:Kapitel 53",
"Zimmerische Chronik Band 1:Kapitel 54",
"Zimmerische Chronik Band 1:Kapitel 55",
"Zimmerische Chronik Band 1:Kapitel 56",
"Zimmerische Chronik Band 1:Kapitel 57",
"Zimmerische Chronik Band 1:Kapitel 58",
"Zimmerische Chronik Band 1:Kapitel 59",
"Zimmerische Chronik Band 1:Kapitel 6",
"Zimmerische Chronik Band 1:Kapitel 60",
"Zimmerische Chronik Band 1:Kapitel 61",
"Zimmerische Chronik Band 1:Kapitel 62",
"Zimmerische Chronik Band 1:Kapitel 63",
"Zimmerische Chronik Band 1:Kapitel 64",
"Zimmerische Chronik Band 1:Kapitel 65",
"Zimmerische Chronik Band 1:Kapitel 66",
"Zimmerische Chronik Band 1:Kapitel 67",
"Zimmerische Chronik Band 1:Kapitel 68",
"Zimmerische Chronik Band 1:Kapitel 69",
"Zimmerische Chronik Band 1:Kapitel 7",
"Zimmerische Chronik Band 1:Kapitel 70",
"Zimmerische Chronik Band 1:Kapitel 71",
"Zimmerische Chronik Band 1:Kapitel 72",
"Zimmerische Chronik Band 1:Kapitel 73",
"Zimmerische Chronik Band 1:Kapitel 74",
"Zimmerische Chronik Band 1:Kapitel 75",
"Zimmerische Chronik Band 1:Kapitel 76",
"Zimmerische Chronik Band 1:Kapitel 77",
"Zimmerische Chronik Band 1:Kapitel 78",
"Zimmerische Chronik Band 1:Kapitel 79",
"Zimmerische Chronik Band 1:Kapitel 8",
"Zimmerische Chronik Band 1:Kapitel 80",
"Zimmerische Chronik Band 1:Kapitel 81",
"Zimmerische Chronik Band 1:Kapitel 82",
"Zimmerische Chronik Band 1:Kapitel 83",
"Zimmerische Chronik Band 1:Kapitel 9",
"Zimmerische Chronik Band 2:Kapitel 1",
"Zimmerische Chronik Band 2:Kapitel 10",
"Zimmerische Chronik Band 2:Kapitel 11",
"Zimmerische Chronik Band 2:Kapitel 12",
"Zimmerische Chronik Band 2:Kapitel 13",
"Zimmerische Chronik Band 2:Kapitel 14",
"Zimmerische Chronik Band 2:Kapitel 15",
"Zimmerische Chronik Band 2:Kapitel 16",
"Zimmerische Chronik Band 2:Kapitel 17",
"Zimmerische Chronik Band 2:Kapitel 18",
"Zimmerische Chronik Band 2:Kapitel 19",
"Zimmerische Chronik Band 2:Kapitel 2",
"Zimmerische Chronik Band 2:Kapitel 20",
"Zimmerische Chronik Band 2:Kapitel 21",
"Zimmerische Chronik Band 2:Kapitel 22",
"Zimmerische Chronik Band 2:Kapitel 23",
"Zimmerische Chronik Band 2:Kapitel 24",
"Zimmerische Chronik Band 2:Kapitel 25",
"Zimmerische Chronik Band 2:Kapitel 26",
"Zimmerische Chronik Band 2:Kapitel 27",
"Zimmerische Chronik Band 2:Kapitel 28",
"Zimmerische Chronik Band 2:Kapitel 29",
"Zimmerische Chronik Band 2:Kapitel 3",
"Zimmerische Chronik Band 2:Kapitel 30",
"Zimmerische Chronik Band 2:Kapitel 31",
"Zimmerische Chronik Band 2:Kapitel 32",
"Zimmerische Chronik Band 2:Kapitel 33",
"Zimmerische Chronik Band 2:Kapitel 34",
"Zimmerische Chronik Band 2:Kapitel 35",
"Zimmerische Chronik Band 2:Kapitel 36",
"Zimmerische Chronik Band 2:Kapitel 37",
"Zimmerische Chronik Band 2:Kapitel 38",
"Zimmerische Chronik Band 2:Kapitel 39",
"Zimmerische Chronik Band 2:Kapitel 4",
"Zimmerische Chronik Band 2:Kapitel 40",
"Zimmerische Chronik Band 2:Kapitel 41",
"Zimmerische Chronik Band 2:Kapitel 42",
"Zimmerische Chronik Band 2:Kapitel 43",
"Zimmerische Chronik Band 2:Kapitel 44",
"Zimmerische Chronik Band 2:Kapitel 45",
"Zimmerische Chronik Band 2:Kapitel 46",
"Zimmerische Chronik Band 2:Kapitel 47",
"Zimmerische Chronik Band 2:Kapitel 48",
"Zimmerische Chronik Band 2:Kapitel 49",
"Zimmerische Chronik Band 2:Kapitel 5",
"Zimmerische Chronik Band 2:Kapitel 50",
"Zimmerische Chronik Band 2:Kapitel 51",
"Zimmerische Chronik Band 2:Kapitel 52",
"Zimmerische Chronik Band 2:Kapitel 53",
"Zimmerische Chronik Band 2:Kapitel 54",
"Zimmerische Chronik Band 2:Kapitel 55",
"Zimmerische Chronik Band 2:Kapitel 56",
"Zimmerische Chronik Band 2:Kapitel 57",
"Zimmerische Chronik Band 2:Kapitel 58",
"Zimmerische Chronik Band 2:Kapitel 59",
"Zimmerische Chronik Band 2:Kapitel 6",
"Zimmerische Chronik Band 2:Kapitel 60",
"Zimmerische Chronik Band 2:Kapitel 61",
"Zimmerische Chronik Band 2:Kapitel 62",
"Zimmerische Chronik Band 2:Kapitel 63",
"Zimmerische Chronik Band 2:Kapitel 7",
"Zimmerische Chronik Band 2:Kapitel 8",
"Zimmerische Chronik Band 2:Kapitel 9",
"Zimmerische Chronik Band 3:Kapitel 1",
"Zimmerische Chronik Band 3:Kapitel 10",
"Zimmerische Chronik Band 3:Kapitel 2",
"Zimmerische Chronik Band 3:Kapitel 3",
"Zimmerische Chronik Band 3:Kapitel 4",
"Zimmerische Chronik Band 3:Kapitel 5",
"Zimmerische Chronik Band 3:Kapitel 6",
"Zimmerische Chronik Band 3:Kapitel 7",
"Zimmerische Chronik Band 3:Kapitel 8",
"Zimmerische Chronik Band 3:Kapitel 9"]

wiki = pywikibot.Site()

for lemma in lemmas:
    page_info = re.search(r'Zimmerische Chronik Band (\d):Kapitel (\d{1,2})', lemma)
    band = page_info.group(1)
    kapitel = page_info.group(2)
    page = pywikibot.Page(wiki, title= lemma)
    template_textdaten = re.search('\{\{Textdaten(?:\{\{.*?\}\}|.)*?\}\}', page.text, re.DOTALL).group()
    template_handler_orig = TemplateHandler(template_textdaten)

    template_navigation = TemplateHandler()
    template_navigation.set_title('Kapitel')

    page_from_orig = template_handler_orig.get_parameter('HERKUNFT')['value']
    #page_from_orig = re.search(r'\d{1,3}(?:–\d{1,3})?', page_from_orig).group()
    list_navigation = []
    try:
        page_from_orig = re.search(r'Band \d. S. ([\dIXV]{1,10}(?: ?–?-? ?[\dIXV]{1,10})?)', page_from_orig).group()
        list_navigation.append({'key': 'SEITE', 'value': page_from_orig})
    except:
        pass

    list_navigation.append({'key': 'HERKUNFT', 'value': "Zimmerische Chronik"})
    try:
        list_navigation.append({'key': 'UNTERTITEL', 'value': template_handler_orig.get_parameter('SUBTITEL')['value']})
    except:
        pass
    list_navigation.append({'key': 'VORIGER', 'value': 'Band '+ band + '/Kapitel ' + str(int(kapitel)-1)})
    list_navigation.append({'key': 'NÄCHSTER', 'value': 'Band '+ band + '/Kapitel ' + str(int(kapitel)+1)})
    list_navigation.append({'key': 'TITELTEIL', 'value': "3"})
    #list_navigation.append({'key': 'ZUSAMMENFASSUNG', 'value': template_handler_orig.get_parameter('KURZBESCHREIBUNG')['value']})
    #list_navigation.append({'key': 'BILD', 'value': template_handler_orig.get_parameter('BILD')['value']})
    list_navigation.append({'key': 'BEARBEITUNGSSTAND', 'value': template_handler_orig.get_parameter('BEARBEITUNGSSTAND')['value']})
    list_navigation.append({'key': 'KATEGORIE', 'value': "Zimmerische Chronik"})

    template_navigation.update_parameters(list_navigation)

    page.text = re.sub('\{\{Textdaten(?:.|\n)*?BEARBEITUNGSSTAND.*\n\}\}', template_navigation.get_str(), page.text)
    page.save(summary= 'Umstellung auf Vorlage Kapitel', botflag= True)
    page.move('Zimmerische Chronik/Band ' + band + '/Kapitel ' + kapitel, reason='Verschiebung des Lemmas für eine bessere Navigation')