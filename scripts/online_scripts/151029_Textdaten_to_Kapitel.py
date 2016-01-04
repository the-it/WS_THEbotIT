# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
from tools.wiki_template_handler.template_handler import TemplateHandler
import re
import pywikibot


lemmas = ["William Shakspeare's sämmtliche Gedichte/Einleitung",
"William Shakspeare's sämmtliche Gedichte/Sonett C",
"William Shakspeare's sämmtliche Gedichte/Sonett CI",
"William Shakspeare's sämmtliche Gedichte/Sonett CII",
"William Shakspeare's sämmtliche Gedichte/Sonett CIII",
"William Shakspeare's sämmtliche Gedichte/Sonett CIV",
"William Shakspeare's sämmtliche Gedichte/Sonett CIX",
"William Shakspeare's sämmtliche Gedichte/Sonett CL",
"William Shakspeare's sämmtliche Gedichte/Sonett CLI",
"William Shakspeare's sämmtliche Gedichte/Sonett CLII",
"William Shakspeare's sämmtliche Gedichte/Sonett CLIII",
"William Shakspeare's sämmtliche Gedichte/Sonett CLIV",
"William Shakspeare's sämmtliche Gedichte/Sonett CV",
"William Shakspeare's sämmtliche Gedichte/Sonett CVI",
"William Shakspeare's sämmtliche Gedichte/Sonett CVII",
"William Shakspeare's sämmtliche Gedichte/Sonett CVIII",
"William Shakspeare's sämmtliche Gedichte/Sonett CX",
"William Shakspeare's sämmtliche Gedichte/Sonett CXI",
"William Shakspeare's sämmtliche Gedichte/Sonett CXII",
"William Shakspeare's sämmtliche Gedichte/Sonett CXIII",
"William Shakspeare's sämmtliche Gedichte/Sonett CXIV",
"William Shakspeare's sämmtliche Gedichte/Sonett CXIX",
"William Shakspeare's sämmtliche Gedichte/Sonett CXL",
"William Shakspeare's sämmtliche Gedichte/Sonett CXLI",
"William Shakspeare's sämmtliche Gedichte/Sonett CXLII",
"William Shakspeare's sämmtliche Gedichte/Sonett CXLIII",
"William Shakspeare's sämmtliche Gedichte/Sonett CXLIV",
"William Shakspeare's sämmtliche Gedichte/Sonett CXLIX",
"William Shakspeare's sämmtliche Gedichte/Sonett CXLV",
"William Shakspeare's sämmtliche Gedichte/Sonett CXLVI",
"William Shakspeare's sämmtliche Gedichte/Sonett CXLVII",
"William Shakspeare's sämmtliche Gedichte/Sonett CXLVIII",
"William Shakspeare's sämmtliche Gedichte/Sonett CXV",
"William Shakspeare's sämmtliche Gedichte/Sonett CXVI",
"William Shakspeare's sämmtliche Gedichte/Sonett CXVII",
"William Shakspeare's sämmtliche Gedichte/Sonett CXVIII",
"William Shakspeare's sämmtliche Gedichte/Sonett CXX",
"William Shakspeare's sämmtliche Gedichte/Sonett CXXI",
"William Shakspeare's sämmtliche Gedichte/Sonett CXXII",
"William Shakspeare's sämmtliche Gedichte/Sonett CXXIII",
"William Shakspeare's sämmtliche Gedichte/Sonett CXXIV",
"William Shakspeare's sämmtliche Gedichte/Sonett CXXIX",
"William Shakspeare's sämmtliche Gedichte/Sonett CXXV",
"William Shakspeare's sämmtliche Gedichte/Sonett CXXVI",
"William Shakspeare's sämmtliche Gedichte/Sonett CXXVII",
"William Shakspeare's sämmtliche Gedichte/Sonett CXXVIII",
"William Shakspeare's sämmtliche Gedichte/Sonett CXXX",
"William Shakspeare's sämmtliche Gedichte/Sonett CXXXI",
"William Shakspeare's sämmtliche Gedichte/Sonett CXXXII",
"William Shakspeare's sämmtliche Gedichte/Sonett CXXXIII",
"William Shakspeare's sämmtliche Gedichte/Sonett CXXXIV",
"William Shakspeare's sämmtliche Gedichte/Sonett CXXXIX",
"William Shakspeare's sämmtliche Gedichte/Sonett CXXXV",
"William Shakspeare's sämmtliche Gedichte/Sonett CXXXVI",
"William Shakspeare's sämmtliche Gedichte/Sonett CXXXVII",
"William Shakspeare's sämmtliche Gedichte/Sonett CXXXVIII",
"William Shakspeare's sämmtliche Gedichte/Sonett I",
"William Shakspeare's sämmtliche Gedichte/Sonett II",
"William Shakspeare's sämmtliche Gedichte/Sonett III",
"William Shakspeare's sämmtliche Gedichte/Sonett IV",
"William Shakspeare's sämmtliche Gedichte/Sonett IX",
"William Shakspeare's sämmtliche Gedichte/Sonett L",
"William Shakspeare's sämmtliche Gedichte/Sonett LI",
"William Shakspeare's sämmtliche Gedichte/Sonett LII",
"William Shakspeare's sämmtliche Gedichte/Sonett LIII",
"William Shakspeare's sämmtliche Gedichte/Sonett LIV",
"William Shakspeare's sämmtliche Gedichte/Sonett LIX",
"William Shakspeare's sämmtliche Gedichte/Sonett LV",
"William Shakspeare's sämmtliche Gedichte/Sonett LVI",
"William Shakspeare's sämmtliche Gedichte/Sonett LVII",
"William Shakspeare's sämmtliche Gedichte/Sonett LVIII",
"William Shakspeare's sämmtliche Gedichte/Sonett LX",
"William Shakspeare's sämmtliche Gedichte/Sonett LXI",
"William Shakspeare's sämmtliche Gedichte/Sonett LXII",
"William Shakspeare's sämmtliche Gedichte/Sonett LXIII",
"William Shakspeare's sämmtliche Gedichte/Sonett LXIV",
"William Shakspeare's sämmtliche Gedichte/Sonett LXIX",
"William Shakspeare's sämmtliche Gedichte/Sonett LXV",
"William Shakspeare's sämmtliche Gedichte/Sonett LXVI",
"William Shakspeare's sämmtliche Gedichte/Sonett LXVII",
"William Shakspeare's sämmtliche Gedichte/Sonett LXVIII",
"William Shakspeare's sämmtliche Gedichte/Sonett LXX",
"William Shakspeare's sämmtliche Gedichte/Sonett LXXI",
"William Shakspeare's sämmtliche Gedichte/Sonett LXXII",
"William Shakspeare's sämmtliche Gedichte/Sonett LXXIII",
"William Shakspeare's sämmtliche Gedichte/Sonett LXXIV",
"William Shakspeare's sämmtliche Gedichte/Sonett LXXIX",
"William Shakspeare's sämmtliche Gedichte/Sonett LXXV",
"William Shakspeare's sämmtliche Gedichte/Sonett LXXVI",
"William Shakspeare's sämmtliche Gedichte/Sonett LXXVII",
"William Shakspeare's sämmtliche Gedichte/Sonett LXXVIII",
"William Shakspeare's sämmtliche Gedichte/Sonett LXXX",
"William Shakspeare's sämmtliche Gedichte/Sonett LXXXI",
"William Shakspeare's sämmtliche Gedichte/Sonett LXXXII",
"William Shakspeare's sämmtliche Gedichte/Sonett LXXXIII",
"William Shakspeare's sämmtliche Gedichte/Sonett LXXXIV",
"William Shakspeare's sämmtliche Gedichte/Sonett LXXXIX",
"William Shakspeare's sämmtliche Gedichte/Sonett LXXXV",
"William Shakspeare's sämmtliche Gedichte/Sonett LXXXVI",
"William Shakspeare's sämmtliche Gedichte/Sonett LXXXVII",
"William Shakspeare's sämmtliche Gedichte/Sonett LXXXVIII",
"William Shakspeare's sämmtliche Gedichte/Sonett V",
"William Shakspeare's sämmtliche Gedichte/Sonett VI",
"William Shakspeare's sämmtliche Gedichte/Sonett VII",
"William Shakspeare's sämmtliche Gedichte/Sonett VIII",
"William Shakspeare's sämmtliche Gedichte/Sonett X",
"William Shakspeare's sämmtliche Gedichte/Sonett XC",
"William Shakspeare's sämmtliche Gedichte/Sonett XCI",
"William Shakspeare's sämmtliche Gedichte/Sonett XCII",
"William Shakspeare's sämmtliche Gedichte/Sonett XCIII",
"William Shakspeare's sämmtliche Gedichte/Sonett XCIV",
"William Shakspeare's sämmtliche Gedichte/Sonett XCIX",
"William Shakspeare's sämmtliche Gedichte/Sonett XCV",
"William Shakspeare's sämmtliche Gedichte/Sonett XCVI",
"William Shakspeare's sämmtliche Gedichte/Sonett XCVII",
"William Shakspeare's sämmtliche Gedichte/Sonett XCVIII",
"William Shakspeare's sämmtliche Gedichte/Sonett XI",
"William Shakspeare's sämmtliche Gedichte/Sonett XII",
"William Shakspeare's sämmtliche Gedichte/Sonett XIII",
"William Shakspeare's sämmtliche Gedichte/Sonett XIV",
"William Shakspeare's sämmtliche Gedichte/Sonett XIX",
"William Shakspeare's sämmtliche Gedichte/Sonett XL",
"William Shakspeare's sämmtliche Gedichte/Sonett XLI",
"William Shakspeare's sämmtliche Gedichte/Sonett XLII",
"William Shakspeare's sämmtliche Gedichte/Sonett XLIII",
"William Shakspeare's sämmtliche Gedichte/Sonett XLIV",
"William Shakspeare's sämmtliche Gedichte/Sonett XLIX",
"William Shakspeare's sämmtliche Gedichte/Sonett XLV",
"William Shakspeare's sämmtliche Gedichte/Sonett XLVI",
"William Shakspeare's sämmtliche Gedichte/Sonett XLVII",
"William Shakspeare's sämmtliche Gedichte/Sonett XLVIII",
"William Shakspeare's sämmtliche Gedichte/Sonett XV",
"William Shakspeare's sämmtliche Gedichte/Sonett XVI",
"William Shakspeare's sämmtliche Gedichte/Sonett XVII",
"William Shakspeare's sämmtliche Gedichte/Sonett XVIII",
"William Shakspeare's sämmtliche Gedichte/Sonett XX",
"William Shakspeare's sämmtliche Gedichte/Sonett XXI",
"William Shakspeare's sämmtliche Gedichte/Sonett XXII",
"William Shakspeare's sämmtliche Gedichte/Sonett XXIII",
"William Shakspeare's sämmtliche Gedichte/Sonett XXIV",
"William Shakspeare's sämmtliche Gedichte/Sonett XXIX",
"William Shakspeare's sämmtliche Gedichte/Sonett XXV",
"William Shakspeare's sämmtliche Gedichte/Sonett XXVI",
"William Shakspeare's sämmtliche Gedichte/Sonett XXVII",
"William Shakspeare's sämmtliche Gedichte/Sonett XXVIII",
"William Shakspeare's sämmtliche Gedichte/Sonett XXX",
"William Shakspeare's sämmtliche Gedichte/Sonett XXXI",
"William Shakspeare's sämmtliche Gedichte/Sonett XXXII",
"William Shakspeare's sämmtliche Gedichte/Sonett XXXIII",
"William Shakspeare's sämmtliche Gedichte/Sonett XXXIV",
"William Shakspeare's sämmtliche Gedichte/Sonett XXXIX",
"William Shakspeare's sämmtliche Gedichte/Sonett XXXV",
"William Shakspeare's sämmtliche Gedichte/Sonett XXXVI",
"William Shakspeare's sämmtliche Gedichte/Sonett XXXVII",
"William Shakspeare's sämmtliche Gedichte/Sonett XXXVIII",
"William Shakspeare's sämmtliche Gedichte/Tarquin und Lucretia",
"William Shakspeare's sämmtliche Gedichte/Venus und Adonis"]

wiki = pywikibot.Site()

for lemma in lemmas:
    page = pywikibot.Page(wiki, title= lemma)
    template_textdaten = re.search('\{\{Textdaten(?:\{\{.*?\}\}|.)*?\}\}', page.text, re.DOTALL).group()
    template_handler_orig = TemplateHandler(template_textdaten)

    template_navigation = TemplateHandler()
    template_navigation.set_title('Kapitel')

    page_from_orig = template_handler_orig.get_parameter('HERKUNFT')['value']
    #page_from_orig = re.search(r'\d{1,3}(?:–\d{1,3})?', page_from_orig).group()
    try:
        page_from_orig = re.search(r'S. (\d{1,3}(?: ?–?-? ?\d{1,3})?)', page_from_orig).group(1)
        list_navigation.append({'key': 'SEITE', 'value': page_from_orig})
    except:
        pass
    list_navigation = []
    list_navigation.append({'key': 'HERKUNFT', 'value': "William Shakspeare's sämmtliche Gedichte"})
    try:
        list_navigation.append({'key': 'UNTERTITEL', 'value': template_handler_orig.get_parameter('SUBTITEL')['value']})
    except:
        pass
    try:
        list_navigation.append({'key': 'VORIGER', 'value': re.sub("William Shakspeare's sämmtliche Gedichte/", '', template_handler_orig.get_parameter('VORIGER')['value'])})
    except:
        pass
    try:
        list_navigation.append({'key': 'NÄCHSTER', 'value': re.sub("William Shakspeare's sämmtliche Gedichte/", '', template_handler_orig.get_parameter('NÄCHSTER')['value'])})
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
    list_navigation.append({'key': 'KATEGORIE', 'value': "William Shakspeare's sämmtliche Gedichte"})

    template_navigation.update_parameters(list_navigation)

    page.text = re.sub('\{\{Textdaten(?:.|\n)*?BEARBEITUNGSSTAND.*\n\}\}', template_navigation.get_str(), page.text)
    page.save(summary= 'Umstellung auf Vorlage Kapitel', botflag= True)
