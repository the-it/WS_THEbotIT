
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

lemmas = ["Christliche Symbolik/Vorwort",
"Christliche Symbolik/Aaron",
"Christliche Symbolik/Aaronswurzel",
"Christliche Symbolik/Aas",
"Christliche Symbolik/Abel",
"Christliche Symbolik/Abendmahl",
"Christliche Symbolik/Abendroth",
"Christliche Symbolik/Abendstern",
"Christliche Symbolik/Abraham",
"Christliche Symbolik/Acht",
"Christliche Symbolik/Acker",
"Christliche Symbolik/Adam",
"Christliche Symbolik/Adler",
"Christliche Symbolik/Advent",
"Christliche Symbolik/Aehre",
"Christliche Symbolik/Aerndte",
"Christliche Symbolik/Agnus dei",
"Christliche Symbolik/Ahasver",
"Christliche Symbolik/Amethyst",
"Christliche Symbolik/Amor",
"Christliche Symbolik/St. Antonius der Grosse",
"Christliche Symbolik/Armuth",
"Christliche Symbolik/Asche",
"Christliche Symbolik/Auferstehung",
"Christliche Symbolik/Burg",
"Christliche Symbolik/Büchse",
"Christliche Symbolik/Charfreitag",
"Christliche Symbolik/Cherubim",
"Christliche Symbolik/St. Christoph",
"Christliche Symbolik/Christus",
"Christliche Symbolik/Chrysam",
"Christliche Symbolik/Crucifix",
"Christliche Symbolik/Drache",
"Christliche Symbolik/Ehe",
"Christliche Symbolik/Engel",
"Christliche Symbolik/Engelwurz",
"Christliche Symbolik/Ente",
"Christliche Symbolik/Epheu",
"Christliche Symbolik/Erdbeben",
"Christliche Symbolik/Erdbeere",
"Christliche Symbolik/Erde",
"Christliche Symbolik/Erstgeburt",
"Christliche Symbolik/Esel",
"Christliche Symbolik/Espe",
"Christliche Symbolik/Essig",
"Christliche Symbolik/Evangelisten",
"Christliche Symbolik/Fass",
"Christliche Symbolik/Fasten",
"Christliche Symbolik/Furien",
"Christliche Symbolik/Fuss",
"Christliche Symbolik/Fünf",
"Christliche Symbolik/Gold",
"Christliche Symbolik/Gott",
"Christliche Symbolik/Grab",
"Christliche Symbolik/Grablegung",
"Christliche Symbolik/Gral",
"Christliche Symbolik/Granate",
"Christliche Symbolik/Haar",
"Christliche Symbolik/Hagebutten",
"Christliche Symbolik/Hammer",
"Christliche Symbolik/Hand",
"Christliche Symbolik/Hexensabbath",
"Christliche Symbolik/Himmel",
"Christliche Symbolik/Hölle",
"Christliche Symbolik/Holz",
"Christliche Symbolik/Honig",
"Christliche Symbolik/Horn",
"Christliche Symbolik/Johannes der Evangelist",
"Christliche Symbolik/Korb",
"Christliche Symbolik/Korn",
"Christliche Symbolik/Koth",
"Christliche Symbolik/Krankheit",
"Christliche Symbolik/Kranz",
"Christliche Symbolik/Kreuz",
"Christliche Symbolik/Krippe",
"Christliche Symbolik/Labyrinth",
"Christliche Symbolik/Leuchter",
"Christliche Symbolik/St. Lucas",
"Christliche Symbolik/St. Lucia",
"Christliche Symbolik/Matthäus",
"Christliche Symbolik/Michael",
"Christliche Symbolik/Mond",
"Christliche Symbolik/Ostern",
"Christliche Symbolik/Pfau",
"Christliche Symbolik/Pfingsten",
"Christliche Symbolik/Pieta",
"Christliche Symbolik/Pilger",
"Christliche Symbolik/Plagen",
"Christliche Symbolik/Platane",
"Christliche Symbolik/Rechts und links",
"Christliche Symbolik/Roth",
"Christliche Symbolik/Rothkehlchen",
"Christliche Symbolik/Sperling",
"Christliche Symbolik/Schnee",
"Christliche Symbolik/Schwere",
"Christliche Symbolik/Schwert",
"Christliche Symbolik/Scorpion",
"Christliche Symbolik/St. Sebastian",
"Christliche Symbolik/Sieben",
"Christliche Symbolik/Siegel",
"Christliche Symbolik/Simeon",
"Christliche Symbolik/Sonne",
"Christliche Symbolik/Sonnenstrahl",
"Christliche Symbolik/Sterne",
"Christliche Symbolik/Teufel",
"Christliche Symbolik/Tod",
"Christliche Symbolik/Todtenkopf",
"Christliche Symbolik/Weihnachten"]

wiki = pywikibot.Site()

for lemma in lemmas:
    page = pywikibot.Page(wiki, title= lemma)
    template_textdaten = re.search('\{\{Textdaten(?:\{\{.*?\}\}|.)*?\}\}', page.text, re.DOTALL).group()
    template_handler_orig = TemplateHandler(template_textdaten)

    template_navigation = TemplateHandler()
    template_navigation.set_title('Kapitel')

    list_navigation = []
    list_navigation.append({'key': 'HERKUNFT', 'value': "Christliche Symbolik"})
    list_navigation.append({'key': 'VORIGER', 'value': re.sub('Christliche Symbolik/', '', template_handler_orig.get_parameter('VORIGER')['value'])})
    list_navigation.append({'key': 'NÄCHSTER', 'value': re.sub('Christliche Symbolik/', '', template_handler_orig.get_parameter('NÄCHSTER')['value'])})
    list_navigation.append({'key': 'TITELTEIL', 'value': "2"})
    #list_navigation.append({'key': 'BILD', 'value': template_handler_orig.get_parameter('BILD')['value']})
    list_navigation.append({'key': 'BEARBEITUNGSSTAND', 'value': template_handler_orig.get_parameter('BEARBEITUNGSSTAND')['value']})
    list_navigation.append({'key': 'KATEGORIE', 'value': 'Christliche Symbolik'})

    template_navigation.update_parameters(list_navigation)

    page.text = re.sub('\{\{Textdaten(?:.|\n)*?\n\}\}', template_navigation.get_str(), page.text)
    page.save(summary= 'Umstellung auf Vorlage Kapitel', botflag= True)
