
# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
from tools.abbyy_xml import AbbyyXML
import pywikibot

wiki = pywikibot.Site()

for i in range(1, 673):
    print(i)
    if i < 10:
        i_str = "00"+str(i)
    elif i < 100:
        i_str = "0"+str(i)
    else:
        i_str = str(i)
    with open("dump/xml_abbyy/BAU14A019910_00000{}.xml".format(i_str), encoding="utf8") as file_pointer:
        reader = AbbyyXML(file_pointer.read())
        with open("dump/result/" + i_str + ".txt", "w", encoding='utf-8') as f:
            f.write(reader.getText())