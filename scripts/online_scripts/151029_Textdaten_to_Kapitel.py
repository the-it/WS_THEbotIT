
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

lemmas = ["Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Anfang eines Einnahme-Verzeichnisses vom J. 1380",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Armenpflege",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Ausgabe-Rechnung vom J. 1334",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Ausgabe-Rechnung vom J. 1338",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Ausgabe-Rechnung vom J. 1344",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Ausgabe-Rechnung vom J. 1346",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Ausgabe-Rechnung vom J. 1349",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Ausgabe-Rechnung vom J. 1353",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Ausgabe-Rechnung vom J. 1376",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Ausgabe-Rechnung vom J. 1383",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Ausgabe-Rechnung vom J. 1385",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Ausgabe-Rechnung vom J. 1390",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Ausgabe-Rechnung vom J. 1394 (Auszug)",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Beilage I.",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Beilage II.",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Beilage III.",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Beilage IV.",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Beilage IX.",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Beilage V.",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Beilage VI.",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Beilage VII.",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Beilage VIII.",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Beilage X.",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Beilage XI.",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Beilage XII.",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Beilage XIII.",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Beilage XIV.",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Beilage XIX.",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Beilage XV.",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Beilage XVI.",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Beilage XVII.",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Beilage XVIII.",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Belagerung der Burg Reifenscheid",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Besoldungen",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Blide eine Wurfmaschine",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Chronologisches Verzeichniss der in den Rechnungen vorkommenden Geldsorten",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Das Aachener Contingent",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Einnahme-Rechnung vom J. 1344",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Einnahme-Rechnung vom J. 1373",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Einnahme-Rechnung vom J. 1385",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Einnahme-Rechnung vom J. 1387",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Einnahme-Rechnung vom J. 1391",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Einnahmen der Stadt Aachen",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Einzelne Monate der Ausgabe-Rechnung vom J. 1391",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Faustkaempfer",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Flagellanten Pest und Juden",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Geschenke an den Koenig",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Geschenke an hohe und hoechste Personen",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Glossar",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Kirchenfeste und Betheiligung",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Kroenung Karls IV",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Kroenung Wenzels",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Landfriedensbund Zerstoerung des Raubschlosses",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Lesung der heiligen Messe",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Meth",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Monatsrechnung aus dem J. 1384",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Monatsrechnungen vom J. 1386",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Nachtrag. Ausgabe-Rechnung vom J. 1333",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Pulvergeschosse",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Rathhausbau und Buergermeister Chorus",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Rechnung Belagerung des Schlosses Reiferscheid im J. 1385",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Rechnung Belagerung des Schlosses zur Dick im J. 1383",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Tagelohn und Preise der Lebensmittel",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Topographie von Aachen nach den Stadt-Rechnungen des 14. Jahrhunderts",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Verhalten der Stadt waehrend Ludwig",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Vollendung des Rathhauses",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Weinkultur und Weinverbrauch",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Zahl der Rechnungen. Sprache. Geldwerth",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Zerstoerung des Schlosses zur Dick",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Zoelle des Landfriedensbundes",
"Aachener Stadtrechnungen aus dem XIV. Jahrhundert/Übergabe der Burg Reiferscheid"]

wiki = pywikibot.Site()

for lemma in lemmas:
    page = pywikibot.Page(wiki, title= lemma)
    template_textdaten = re.search('\{\{Textdaten(?:\{\{.*?\}\}|.)*?\}\}', page.text, re.DOTALL).group()
    template_handler_orig = TemplateHandler(template_textdaten)

    template_navigation = TemplateHandler()
    template_navigation.set_title('Kapitel')

    list_navigation = []
    list_navigation.append({'key': 'HERKUNFT', 'value': "Aachener Stadtrechnungen aus dem XIV. Jahrhundert"})
    list_navigation.append({'key': 'VORIGER', 'value': re.sub('Aachener Stadtrechnungen aus dem XIV\. Jahrhundert/', '', template_handler_orig.get_parameter('VORIGER')['value'])})
    list_navigation.append({'key': 'NÄCHSTER', 'value': re.sub('Aachener Stadtrechnungen aus dem XIV\. Jahrhundert/', '', template_handler_orig.get_parameter('NÄCHSTER')['value'])})
    list_navigation.append({'key': 'TITELTEIL', 'value': '2'})
    list_navigation.append({'key': 'BILD', 'value': template_handler_orig.get_parameter('BILD')['value']})
    list_navigation.append({'key': 'BEARBEITUNGSSTAND', 'value': 'fertig'})
    list_navigation.append({'key': 'KATEGORIE', 'value': 'Aachener Stadtrechnungen'})

    template_navigation.update_parameters(list_navigation)

    page.text = re.sub('\{\{Textdaten(?:.|\n)*?\n\}\}', template_navigation.get_str(), page.text)
    page.save(summary= 'Umstellung auf Vorlage Kapitel', botflag= True)
