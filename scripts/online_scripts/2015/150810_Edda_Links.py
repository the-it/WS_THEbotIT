# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
from tools.catscan import PetScan
import re
import requests
import pywikibot

test_sites = ['Die Edda (Simrock 1876)/Ältere Edda/Völuspâ'
,'Die Edda (Simrock 1876)/Ältere Edda/Grimnismâl']

sites = ['Seite:Die Edda (1876).djvu/011',
'Seite:Die Edda (1876).djvu/012',
'Seite:Die Edda (1876).djvu/013',
'Seite:Die Edda (1876).djvu/014',
'Seite:Die Edda (1876).djvu/015',
'Seite:Die Edda (1876).djvu/016',
'Seite:Die Edda (1876).djvu/017',
'Seite:Die Edda (1876).djvu/018',
'Seite:Die Edda (1876).djvu/019',
'Seite:Die Edda (1876).djvu/021',
'Seite:Die Edda (1876).djvu/022',
'Seite:Die Edda (1876).djvu/023',
'Seite:Die Edda (1876).djvu/024',
'Seite:Die Edda (1876).djvu/025',
'Seite:Die Edda (1876).djvu/026',
'Seite:Die Edda (1876).djvu/027',
'Seite:Die Edda (1876).djvu/030',
'Seite:Die Edda (1876).djvu/031',
'Seite:Die Edda (1876).djvu/032',
'Seite:Die Edda (1876).djvu/033',
'Seite:Die Edda (1876).djvu/034',
'Seite:Die Edda (1876).djvu/035',
'Seite:Die Edda (1876).djvu/036',
'Seite:Die Edda (1876).djvu/037',
'Seite:Die Edda (1876).djvu/038',
'Seite:Die Edda (1876).djvu/039',
'Seite:Die Edda (1876).djvu/040',
'Seite:Die Edda (1876).djvu/041',
'Seite:Die Edda (1876).djvu/042',
'Seite:Die Edda (1876).djvu/044',
'Seite:Die Edda (1876).djvu/070',
'Seite:Die Edda (1876).djvu/074',
'Seite:Die Edda (1876).djvu/076',
'Seite:Die Edda (1876).djvu/080',
'Seite:Die Edda (1876).djvu/081',
'Seite:Die Edda (1876).djvu/086',
'Seite:Die Edda (1876).djvu/087',
'Seite:Die Edda (1876).djvu/088',
'Seite:Die Edda (1876).djvu/089',
'Seite:Die Edda (1876).djvu/099',
'Seite:Die Edda (1876).djvu/101',
'Seite:Die Edda (1876).djvu/102',
'Seite:Die Edda (1876).djvu/130',
'Seite:Die Edda (1876).djvu/131',
'Seite:Die Edda (1876).djvu/193']

site = pywikibot.Site('de', 'wikisource')
for lemma in sites:

    page = pywikibot.Page(site, lemma)
    to_change = page.text
    to_change = re.sub('\[\[Edda', '[[Die Edda (Simrock 1876)', to_change)
    page.text = to_change
    page.save('Umbennenung aller Links von "Edda" zu "Die Edda (Simrock 1876)"')