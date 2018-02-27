# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
from tools.wiki_template_handler.template_handler import TemplateHandler
import re
import pywikibot


lemmas = ["Hände (Březina)/Antworten",
"Hände (Březina)/Der stille Ozean",
"Hände (Březina)/Die Zeit",
"Hände (Březina)/Dithyrambus der Welten",
"Hände (Březina)/Es sangen die Wässer",
"Hände (Březina)/Es sangen die brennenden Sterne",
"Hände (Březina)/Frauen",
"Hände (Březina)/Frühlingsnacht",
"Hände (Březina)/Gluten",
"Hände (Březina)/Hände",
"Hände (Březina)/Musik der Blinden",
"Hände (Březina)/Orte der Harmonie und der Versöhnung",
"Hände (Březina)/Prolog",
"Hände (Březina)/Reiner Morgen",
"Hände (Březina)/Rundgesang der Herzen",
"Hände (Březina)/Schmerz des Menschen",
"Hände (Březina)/Totenwache",
"Hände (Březina)/Vorwort",
"Hände (Březina)/Wahnbetörte",
"Hände (Březina)/Wir beben vor der Macht des Willens"]

wiki = pywikibot.Site()

for lemma in lemmas:
    page = pywikibot.Page(wiki, title= lemma)
    template_textdaten = re.search('\{\{Textdaten(?:\{\{.*?\}\}|.)*?\}\}', page.text, re.DOTALL).group()
    template_handler_orig = TemplateHandler(template_textdaten)

    template_navigation = TemplateHandler()
    template_navigation.set_title('Kapitel')

    page_from_orig = template_handler_orig.get_parameter('HERKUNFT')['value']
    #page_from_orig = re.search(r'\d{1,3}(?:–\d{1,3})?', page_from_orig).group()
    list_navigation = []
    page_from_orig = re.search(r'S. (\d{1,3}(?: ?–?-? ?\d{1,3})?)', page_from_orig).group(1)
    list_navigation.append({'key': 'SEITE', 'value': page_from_orig})
    try:
        list_navigation.append({'key': 'ANMERKUNG', 'value': 'Origninaltitel: ' + template_handler_orig.get_parameter('ORIGINALTITEL')['value']})
    except:
        pass
    list_navigation.append({'key': 'HERKUNFT', 'value': "Hände (Březina)"})
    #try:
    #    list_navigation.append({'key': 'UNTERTITEL', 'value': template_handler_orig.get_parameter('SUBTITEL')['value']})
    #except:
    #    pass
    try:
        list_navigation.append({'key': 'VORIGER', 'value': re.sub("Hände \(Březina\)/", '', template_handler_orig.get_parameter('VORIGER')['value'])})
    except:
        pass
    try:
        list_navigation.append({'key': 'NÄCHSTER', 'value': re.sub("Hände \(Březina\)/", '', template_handler_orig.get_parameter('NÄCHSTER')['value'])})
    except:
        pass
    list_navigation.append({'key': 'TITELTEIL', 'value': "2"})
    #list_navigation.append({'key': 'ZUSAMMENFASSUNG', 'value': template_handler_orig.get_parameter('KURZBESCHREIBUNG')['value']})
    try:
        list_navigation.append({'key': 'WIKIPEDIA', 'value': template_handler_orig.get_parameter('WIKIPEDIA')['value']})
    except:
        pass
    #list_navigation.append({'key': 'BILD', 'value': template_handler_orig.get_parameter('BILD')['value']})
    list_navigation.append({'key': 'BEARBEITUNGSSTAND', 'value': template_handler_orig.get_parameter('BEARBEITUNGSSTAND')['value']})
    list_navigation.append({'key': 'KATEGORIE', 'value': "Brezina Hände 1908"})

    template_navigation.update_parameters(list_navigation)

    page.text = re.sub('\{\{Textdaten(?:\{\{.*?\}\}|.)*?\}\}', template_navigation.get_str(), page.text, flags = re.DOTALL)
    page.save(summary= 'Umstellung auf Vorlage Kapitel', botflag= True)
