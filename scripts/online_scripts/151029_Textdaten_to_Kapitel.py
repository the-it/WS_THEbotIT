# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
from tools.wiki_template_handler.template_handler import TemplateHandler
import re
import pywikibot


lemmas = ["Der Vampir (Reymont)/Achtes Kapitel",
"Der Vampir (Reymont)/Drittes Kapitel",
"Der Vampir (Reymont)/Erstes Kapitel",
"Der Vampir (Reymont)/Fünftes Kapitel",
"Der Vampir (Reymont)/Neuntes Kapitel",
"Der Vampir (Reymont)/Sechstes Kapitel",
"Der Vampir (Reymont)/Siebentes Kapitel",
"Der Vampir (Reymont)/Viertes Kapitel",
"Der Vampir (Reymont)/Zweites Kapitel"]

wiki = pywikibot.Site()

for lemma in lemmas:
    page = pywikibot.Page(wiki, title= lemma)
    template_textdaten = re.search('\{\{Textdaten(?:\{\{.*?\}\}|.)*?\}\}', page.text, re.DOTALL).group()
    template_handler_orig = TemplateHandler(template_textdaten)

    template_navigation = TemplateHandler()
    template_navigation.set_title('Kapitel')

    page_from_orig = template_handler_orig.get_parameter('HERKUNFT')['value']
    page_from_orig = re.search(r'\d{1,3}(?:–\d{1,3})?', page_from_orig).group()

    list_navigation = []
    list_navigation.append({'key': 'HERKUNFT', 'value': "Der Vampir (Reymont)"})
    list_navigation.append({'key': 'SEITE', 'value': page_from_orig})
    try:
        list_navigation.append({'key': 'VORIGER', 'value': re.sub('Der Vampir (Reymont)/', '', template_handler_orig.get_parameter('VORIGER')['value'])})
        list_navigation.append({'key': 'NÄCHSTER', 'value': re.sub('Der Vampir (Reymont)/', '', template_handler_orig.get_parameter('NÄCHSTER')['value'])})
    except:
        pass
    list_navigation.append({'key': 'TITELTEIL', 'value': "2"})
    #list_navigation.append({'key': 'BILD', 'value': template_handler_orig.get_parameter('BILD')['value']})
    list_navigation.append({'key': 'BEARBEITUNGSSTAND', 'value': template_handler_orig.get_parameter('BEARBEITUNGSSTAND')['value']})
    list_navigation.append({'key': 'KATEGORIE', 'value': 'Der Vampir (Reymont)'})

    template_navigation.update_parameters(list_navigation)

    page.text = re.sub('\{\{Textdaten(?:.|\n)*?\n\}\}', template_navigation.get_str(), page.text)
    page.save(summary= 'Umstellung auf Vorlage Kapitel', botflag= True)
