
# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
from tools.wiki_template_handler.template_handler import TemplateHandler
import re
import pywikibot

def magazine(number, first_page, last_page):
    title_handler = TemplateHandler()
    title_handler.set_title("Textdaten")
    handler_dict = {}

def volume(page_dict, year):
    pass

year_1853 = {1853: {"first_page": [1, 9, 21, 33, 45, 55, 67, 75, 87, 97, 109, 121, 133, 143, 155, 167, 177, 189, 199, 207, 219, 229, 241, 251,
              263, 273, 285, 297, 309, 321, 331, 343, 355, 363, 373, 383, 393, 405, 417, 429, 441, 453, 463, 475, 485,
              497, 509, 521, 533, 545, 557, 569], "last_page": 576}}

wiki = pywikibot.Site()




pass

# {{Textdaten
# |VORIGER=
# |NÄCHSTER=Die Gartenlaube (1853)/Heft 2
# |AUTOR=Verschiedene
# |TITEL=Die Gartenlaube
# |SUBTITEL=''Illustrirtes Familienblatt''
# |HERKUNFT=off
# |HERAUSGEBER=[[Ernst Keil]]
# |AUFLAGE=
# |ENTSTEHUNGSJAHR=1853
# |ERSCHEINUNGSJAHR=1853
# |ERSCHEINUNGSORT=Leipzig
# |VERLAG=Ernst Keil
# |ÜBERSETZER=
# |ORIGINALTITEL=
# |ORIGINALSUBTITEL=
# |ORIGINALHERKUNFT=
# |WIKIPEDIA=Die Gartenlaube
# |BILD=Die Gartenlaube (1853) 001.jpg
# |QUELLE=[[commons:category:Gartenlaube (1853)|commons]]
# |KURZBESCHREIBUNG=
# |SONSTIGES=
# |BEARBEITUNGSSTAND=fertig
# |BENUTZERHILFE=
# |INDEXSEITE=Die Gartenlaube (1853)
# |GND=
# }}
#
# {{BlockSatzStart}}
# __TOC__
# {{SeitePR|1|Die Gartenlaube (1853) 001.jpg}}
# {{SeitePR|2|Die Gartenlaube (1853) 002.jpg}}
# {{SeitePR|3|Die Gartenlaube (1853) 003.jpg}}
# {{SeitePR|4|Die Gartenlaube (1853) 004.jpg}}
# {{SeitePR|5|Die Gartenlaube (1853) 005.jpg}}
# {{SeitePR|6|Die Gartenlaube (1853) 006.jpg}}
# {{SeitePR|7|Die Gartenlaube (1853) 007.jpg}}
# {{SeitePR|8|Die Gartenlaube (1853) 008.jpg}}
# {{references|x}}
#
# {{references|TIT|WS}}
# {{BlockSatzEnd}}
#
# [[Kategorie:1840er Jahre]]
# [[Kategorie:Deutschland]]
# [[Kategorie:Neuhochdeutsch]]
# [[Kategorie:Illustrierte Werke]]
# [[Kategorie:Die Gartenlaube (1853) Hefte| 01]]
