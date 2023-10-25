# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
import re
import pywikibot
from pywikibot import proofreadpage

files = ["Datei:Squelette_gorille.png",
"Datei:Negrid_types.jpg",
"Datei:Skelett_(Meyers).jpg",
"Datei:Muskeln_des_Beines_(Meyers).jpg",
"Datei:Verdauungsapparates_(Meyers).jpg",
"Datei:Weiblichen_Beckenorgane_(Meyers).jpg",
"Datei:Meyers_Blitz-Lexikon_ethnic_groups.jpg",
"Datei:Mongoloid_types.jpg",
"Datei:LA2-Blitz-0084_ei.jpg",
"Datei:LA2-Blitz-0062_chromosom.jpg",
"Datei:LA2-Blitz-0050_brille_1.jpg",
"Datei:LA2-Blitz-0050_brille_2.jpg",
"Datei:LA2-Blitz-0027_auge.jpg",
"Datei:LA2-Blitz-0034_batikdruck.jpg",
"Datei:LA2-Blitz-0007_afrika_1.jpg",
"Datei:LA2-Blitz-0007_afrika_2.jpg",
"Datei:LA2-Blitz-0007_afrika_3.jpg",
"Datei:Eaqstbalt.JPG",
"Datei:LA2-Blitz-0007_affen.jpg",
"Datei:Kehlkopf_(Meyers).jpg",
"Datei:Kreislauf_des_blutes_(Meyers).jpg",
"Datei:Innerer_Gehoergang_(Meyers).jpg",
"Datei:Gehirn_(Meyers).jpg",
"Datei:Haut(_Meyers).jpg",
"Datei:Bakterien_MBL1932.png"]

site = pywikibot.Site()

fit_datei = re.compile("\[\[(?:Category)?(?:Kategorie)?:Meyers Blitz-Lexikon\]\]")

for i, name in enumerate(files):
    print(i, "/", len(files), name)
    page = pywikibot.Page(site, name)
    #statuspage = proofreadpage.ProofreadPage(site, 'Seite:LA2-Blitz-{}.jpg'.format(add_zeros(i, 4)))
    fit1 = fit_datei.search(page.text)
    if fit1:
        tempText = fit_datei.sub("[[Kategorie:Meyers Blitz-Lexikon/Biologie‎]]", page.text)
        page.text = tempText
        #print(tempText)
        page.save(summary='bot edit: automatisch in eigene Kategorie verschieben.', botflag=True, )
        page.change_category()