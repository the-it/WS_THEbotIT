# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
from tools.wiki_template_handler.template_handler import TemplateHandler
import re
import pywikibot


lemmas = ["Der Hexenhammer (1923)/Dritter Teil, Achtzehnte Frage",
"Der Hexenhammer (1923)/Dritter Teil, Dreiunddreißigste Frage",
"Der Hexenhammer (1923)/Dritter Teil, Dreiundzwanzigste Frage",
"Der Hexenhammer (1923)/Dritter Teil, Dreizehnte Frage",
"Der Hexenhammer (1923)/Dritter Teil, Dreißigste Frage",
"Der Hexenhammer (1923)/Dritter Teil, Dritte Frage",
"Der Hexenhammer (1923)/Dritter Teil, Dritter Teil",
"Der Hexenhammer (1923)/Dritter Teil, Einleitung",
"Der Hexenhammer (1923)/Dritter Teil, Einunddreißigste Frage",
"Der Hexenhammer (1923)/Dritter Teil, Einundzwanzigste Frage",
"Der Hexenhammer (1923)/Dritter Teil, Elfte Frage",
"Der Hexenhammer (1923)/Dritter Teil, Erste Frage",
"Der Hexenhammer (1923)/Dritter Teil, Fünfte Frage",
"Der Hexenhammer (1923)/Dritter Teil, Fünfunddreißigste Frage",
"Der Hexenhammer (1923)/Dritter Teil, Fünfundzwanzigste Frage",
"Der Hexenhammer (1923)/Dritter Teil, Fünfzehnte Frage",
"Der Hexenhammer (1923)/Dritter Teil, Neunte Frage",
"Der Hexenhammer (1923)/Dritter Teil, Neunundzwanzigste Frage",
"Der Hexenhammer (1923)/Dritter Teil, Neunzehnte Frage",
"Der Hexenhammer (1923)/Dritter Teil, Sechste Frage",
"Der Hexenhammer (1923)/Dritter Teil, Sechsundzwanzigste Frage",
"Der Hexenhammer (1923)/Dritter Teil, Sechzehnte Frage",
"Der Hexenhammer (1923)/Dritter Teil, Siebente Frage",
"Der Hexenhammer (1923)/Dritter Teil, Siebenundzwanzigste Frage",
"Der Hexenhammer (1923)/Dritter Teil, Siebzehnte Frage",
"Der Hexenhammer (1923)/Dritter Teil, Vierte Frage",
"Der Hexenhammer (1923)/Dritter Teil, Vierunddreißigste Frage",
"Der Hexenhammer (1923)/Dritter Teil, Vierundzwanzigste Frage",
"Der Hexenhammer (1923)/Dritter Teil, Vierzehnte Frage",
"Der Hexenhammer (1923)/Dritter Teil, Zehnte Frage",
"Der Hexenhammer (1923)/Dritter Teil, Zwanzigste Frage",
"Der Hexenhammer (1923)/Dritter Teil, Zweite Frage",
"Der Hexenhammer (1923)/Dritter Teil, Zweiunddreißigste Frage",
"Der Hexenhammer (1923)/Dritter Teil, Zweiundzwanzigste Frage",
"Der Hexenhammer (1923)/Dritter Teil, Zwölfte Frage",
"Der Hexenhammer (1923)/Erster Teil",
"Der Hexenhammer (1923)/Erster Teil, Achte Frage",
"Der Hexenhammer (1923)/Erster Teil, Achtzehnte Frage",
"Der Hexenhammer (1923)/Erster Teil, Dreizehnte Frage",
"Der Hexenhammer (1923)/Erster Teil, Dritte Frage",
"Der Hexenhammer (1923)/Erster Teil, Einleitung",
"Der Hexenhammer (1923)/Erster Teil, Elfte Frage",
"Der Hexenhammer (1923)/Erster Teil, Erste Frage",
"Der Hexenhammer (1923)/Erster Teil, Fünfte Frage",
"Der Hexenhammer (1923)/Erster Teil, Fünfzehnte Frage",
"Der Hexenhammer (1923)/Erster Teil, Neunte Frage",
"Der Hexenhammer (1923)/Erster Teil, Sechste Frage",
"Der Hexenhammer (1923)/Erster Teil, Sechzehnte Frage",
"Der Hexenhammer (1923)/Erster Teil, Siebente Frage",
"Der Hexenhammer (1923)/Erster Teil, Siebzehnte Frage",
"Der Hexenhammer (1923)/Erster Teil, Vierte Frage",
"Der Hexenhammer (1923)/Erster Teil, Vierzehnte Frage",
"Der Hexenhammer (1923)/Erster Teil, Zehnte Frage",
"Der Hexenhammer (1923)/Erster Teil, Zweite Frage",
"Der Hexenhammer (1923)/Erster Teil, Zwölfte Frage",
"Der Hexenhammer (1923)/Index",
"Der Hexenhammer (1923)/Zweiter Teil",
"Der Hexenhammer (1923)/Zweiter Teil, Erste Frage",
"Der Hexenhammer (1923)/Zweiter Teil, Erste Frage, Kapitel 1",
"Der Hexenhammer (1923)/Zweiter Teil, Erste Frage, Kapitel 10",
"Der Hexenhammer (1923)/Zweiter Teil, Erste Frage, Kapitel 11",
"Der Hexenhammer (1923)/Zweiter Teil, Erste Frage, Kapitel 12",
"Der Hexenhammer (1923)/Zweiter Teil, Erste Frage, Kapitel 13",
"Der Hexenhammer (1923)/Zweiter Teil, Erste Frage, Kapitel 14",
"Der Hexenhammer (1923)/Zweiter Teil, Erste Frage, Kapitel 15",
"Der Hexenhammer (1923)/Zweiter Teil, Erste Frage, Kapitel 16",
"Der Hexenhammer (1923)/Zweiter Teil, Erste Frage, Kapitel 2",
"Der Hexenhammer (1923)/Zweiter Teil, Erste Frage, Kapitel 3",
"Der Hexenhammer (1923)/Zweiter Teil, Erste Frage, Kapitel 4",
"Der Hexenhammer (1923)/Zweiter Teil, Erste Frage, Kapitel 5",
"Der Hexenhammer (1923)/Zweiter Teil, Erste Frage, Kapitel 6",
"Der Hexenhammer (1923)/Zweiter Teil, Erste Frage, Kapitel 7",
"Der Hexenhammer (1923)/Zweiter Teil, Erste Frage, Kapitel 8",
"Der Hexenhammer (1923)/Zweiter Teil, Erste Frage, Kapitel 9",
"Der Hexenhammer (1923)/Zweiter Teil, Zweite Frage",
"Der Hexenhammer (1923)/Zweiter Teil, Zweite Frage, Kapitel I",
"Der Hexenhammer (1923)/Zweiter Teil, Zweite Frage, Kapitel II",
"Der Hexenhammer (1923)/Zweiter Teil, Zweite Frage, Kapitel III",
"Der Hexenhammer (1923)/Zweiter Teil, Zweite Frage, Kapitel IV",
"Der Hexenhammer (1923)/Zweiter Teil, Zweite Frage, Kapitel V",
"Der Hexenhammer (1923)/Zweiter Teil, Zweite Frage, Kapitel VI",
"Der Hexenhammer (1923)/Zweiter Teil, Zweite Frage, Kapitel VII",
"Der Hexenhammer (1923)/Zweiter Teil, Zweite Frage, Kapitel VIII"]

wiki = pywikibot.Site()

for lemma in lemmas:
    page = pywikibot.Page(wiki, title= lemma)
    template_textdaten = re.search('\{\{Textdaten(?:\{\{.*?\}\}|.)*?\}\}', page.text, re.DOTALL).group()
    template_handler_orig = TemplateHandler(template_textdaten)

    template_navigation = TemplateHandler()
    template_navigation.set_title('Kapitel')

    #page_from_orig = template_handler_orig.get_parameter('HERKUNFT')['value']
    #page_from_orig = re.search(r'\d{1,3}(?:–\d{1,3})?', page_from_orig).group()

    list_navigation = []
    list_navigation.append({'key': 'HERKUNFT', 'value': "Der Hexenhammer (1923)"})
    #try:
    #    list_navigation.append({'key': 'UNTERTITEL', 'value': template_handler_orig.get_parameter('SUBTITEL')['value']})
    #except:
    #    pass
    #list_navigation.append({'key': 'SEITE', 'value': page_from_orig})
    try:
        list_navigation.append({'key': 'VORIGER', 'value': re.sub('Der Hexenhammer \(1923\)/', '', template_handler_orig.get_parameter('VORIGER')['value'])})
    except:
        pass
    try:
        list_navigation.append({'key': 'NÄCHSTER', 'value': re.sub('Der Hexenhammer \(1923\)/', '', template_handler_orig.get_parameter('NÄCHSTER')['value'])})
    except:
        pass
    list_navigation.append({'key': 'TITELTEIL', 'value': "2"})
    #list_navigation.append({'key': 'ZUSAMMENFASSUNG', 'value': template_handler_orig.get_parameter('KURZBESCHREIBUNG')['value']})
    #try:
    #    list_navigation.append({'key': 'WIKIPEDIA', 'value': template_handler_orig.get_parameter('WIKIPEDIA')['value']})
    #except:
    #    pass
    list_navigation.append({'key': 'BILD', 'value': template_handler_orig.get_parameter('BILD')['value']})
    list_navigation.append({'key': 'BEARBEITUNGSSTAND', 'value': template_handler_orig.get_parameter('BEARBEITUNGSSTAND')['value']})
    list_navigation.append({'key': 'KATEGORIE', 'value': 'Hexenhammersprenger1923'})

    template_navigation.update_parameters(list_navigation)

    page.text = re.sub('\{\{Textdaten(?:.|\n)*?BEARBEITUNGSSTAND.*\}\}', template_navigation.get_str(), page.text)
    page.save(summary= 'Umstellung auf Vorlage Kapitel', botflag= True)
