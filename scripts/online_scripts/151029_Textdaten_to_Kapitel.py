
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

lemmas = ["Der Todesgang des armenischen Volkes/Dritter Teil/Fünftes Kapitel",
"Der Todesgang des armenischen Volkes/Dritter Teil/Viertes Kapitel",
"Der Todesgang des armenischen Volkes/Dritter Teil/Zweites Kapitel",
"Der Todesgang des armenischen Volkes/Erster Teil",
"Der Todesgang des armenischen Volkes/Erster Teil/Erstes Kapitel",
"Der Todesgang des armenischen Volkes/Erster Teil/Erstes Kapitel/Dritter Teil",
"Der Todesgang des armenischen Volkes/Erster Teil/Erstes Kapitel/Dritter Teil/Erster Abschnitt",
"Der Todesgang des armenischen Volkes/Erster Teil/Erstes Kapitel/Dritter Teil/Zweiter Abschnitt",
"Der Todesgang des armenischen Volkes/Erster Teil/Erstes Kapitel/Erster Teil",
"Der Todesgang des armenischen Volkes/Erster Teil/Erstes Kapitel/Erster Teil/Dritter Abschnitt",
"Der Todesgang des armenischen Volkes/Erster Teil/Erstes Kapitel/Erster Teil/Erster Abschnitt",
"Der Todesgang des armenischen Volkes/Erster Teil/Erstes Kapitel/Erster Teil/Vierter Abschnitt",
"Der Todesgang des armenischen Volkes/Erster Teil/Erstes Kapitel/Erster Teil/Zweiter Abschnitt",
"Der Todesgang des armenischen Volkes/Erster Teil/Erstes Kapitel/Zweiter Teil",
"Der Todesgang des armenischen Volkes/Erster Teil/Erstes Kapitel/Zweiter Teil/Dritter Abschnitt",
"Der Todesgang des armenischen Volkes/Erster Teil/Erstes Kapitel/Zweiter Teil/Erster Abschnitt",
"Der Todesgang des armenischen Volkes/Erster Teil/Erstes Kapitel/Zweiter Teil/Fünfter Abschnitt",
"Der Todesgang des armenischen Volkes/Erster Teil/Erstes Kapitel/Zweiter Teil/Sechster Abschnitt",
"Der Todesgang des armenischen Volkes/Erster Teil/Erstes Kapitel/Zweiter Teil/Siebter Abschnitt",
"Der Todesgang des armenischen Volkes/Erster Teil/Erstes Kapitel/Zweiter Teil/Vierter Abschnitt",
"Der Todesgang des armenischen Volkes/Erster Teil/Erstes Kapitel/Zweiter Teil/Zweiter Abschnitt",
"Der Todesgang des armenischen Volkes/Erster Teil/Zweites Kapitel",
"Der Todesgang des armenischen Volkes/Titel",
"Der Todesgang des armenischen Volkes/Vorwort",
"Der Todesgang des armenischen Volkes/Zweiter Teil",
"Der Todesgang des armenischen Volkes/Zweiter Teil/Achtes Kapitel",
"Der Todesgang des armenischen Volkes/Zweiter Teil/Drittes Kapitel",
"Der Todesgang des armenischen Volkes/Zweiter Teil/Erstes Kapitel",
"Der Todesgang des armenischen Volkes/Zweiter Teil/Fünftes Kapitel",
"Der Todesgang des armenischen Volkes/Zweiter Teil/Neuntes Kapitel",
"Der Todesgang des armenischen Volkes/Zweiter Teil/Sechstes Kapitel",
"Der Todesgang des armenischen Volkes/Zweiter Teil/Siebtes Kapitel",
"Der Todesgang des armenischen Volkes/Zweiter Teil/Viertes Kapitel",
"Der Todesgang des armenischen Volkes/Zweiter Teil/Zweites Kapitel"]

wiki = pywikibot.Site()

for lemma in lemmas:
    page = pywikibot.Page(wiki, title= lemma)
    template_textdaten = re.search('\{\{Textdaten(?:\{\{.*?\}\}|.)*?\}\}', page.text, re.DOTALL).group()
    template_handler_orig = TemplateHandler(template_textdaten)

    template_navigation = TemplateHandler()
    template_navigation.set_title('Kapitel')

    counter = 0
    for character in lemma:
        if character is "/":
            counter += 1

    list_navigation = []
    list_navigation.append({'key': 'HERKUNFT', 'value': "Der Todesgang des armenischen Volkes"})
    list_navigation.append({'key': 'VORIGER', 'value': re.sub('Der Todesgang des armenischen Volkes/', '', template_handler_orig.get_parameter('VORIGER')['value'])})
    list_navigation.append({'key': 'NÄCHSTER', 'value': re.sub('Der Todesgang des armenischen Volkes/', '', template_handler_orig.get_parameter('NÄCHSTER')['value'])})
    list_navigation.append({'key': 'TITELTEIL', 'value': str(counter + 1)})
    list_navigation.append({'key': 'BILD', 'value': template_handler_orig.get_parameter('BILD')['value']})
    list_navigation.append({'key': 'BEARBEITUNGSSTAND', 'value': 'fertig'})
    list_navigation.append({'key': 'KATEGORIE', 'value': 'Kategorie:Der Todesgang des armenischen Volkes'})

    template_navigation.update_parameters(list_navigation)

    page.text = re.sub('\{\{Textdaten(?:.|\n)*?\n\}\}', template_navigation.get_str(), page.text)
    page.save(summary= 'Umstellung auf Vorlage Kapitel', botflag= True)
