
# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
from tools.abbyy_xml import AbbyyXML
import pywikibot

wiki = pywikibot.Site()

for i in range(577, 665):
    print(i)
    page = pywikibot.Page(wiki, 'Seite:Wackernagel Geschichte der Stadt Basel Band 3.pdf/' + str(i))
    if i < 100:
        i_str = "0"+str(i)
    else:
        i_str = str(i)
    with open("dump/xml_abbyy/BAU14A019930_00000{}.xml".format(i_str), encoding="utf8") as file_pointer:
        reader = AbbyyXML(file_pointer.read())

        starter = '<noinclude><pagequality level="1" user="THEbotIT" /><div class="pagetext">{{Seitenstatus2|[[Rudolf Wackernagel]]|[[Geschichte der Stadt Basel. Dritter Band]]|Wackernagel Geschichte der Stadt Basel|}}{{BlockSatzStart}}\n\n\n</noinclude>'

        finisher = "<noinclude>{{BlockSatzEnd}}{{Zitierempfehlung|Projekt=[[Rudolf Wackernagel]]: ''[[Geschichte der Stadt Basel. Dritter Band]]''. Helbing & Lichtenhahn, Basel 1924|Seite=%s*}}</div></noinclude>\n" % (i-545)

        page.text = starter + reader.getText() + finisher
        page.save(summary= 'automatische Seitenerstellung', botflag= True)