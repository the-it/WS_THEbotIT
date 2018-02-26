# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
from tools.catscan import PetScan
import re
import requests
import pywikibot

test_sites = ['Edda',
              'Edda/Erläuterungen/Anmerkungen']

sites = ['Edda/Erläuterungen/Einleitung',
         'Edda/Register',
         'Edda/Snorra-Edda/Aus der Skalda',
         'Edda/Snorra-Edda/Bragarœdhur',
         'Edda/Snorra-Edda/Gylfaginnîng',
         'Edda/Snorra-Edda/Sôlarliôth',
         'Edda/Ältere Edda/Alvîssmâl',
         'Edda/Ältere Edda/Atlakvidha',
         'Edda/Ältere Edda/Atlamâl',
         'Edda/Ältere Edda/Brot af Brynhildarkvidhu',
         'Edda/Ältere Edda/Drâp Niflunga',
         'Edda/Ältere Edda/Fafnismâl',
         'Edda/Ältere Edda/Fiölsvinnsmâl',
         'Edda/Ältere Edda/Grimnismâl',
         'Edda/Ältere Edda/Grôgaldr',
         'Edda/Ältere Edda/Gudhrûnarhvöt',
         'Edda/Ältere Edda/Gudhrûnarkvidha fyrsta',
         'Edda/Ältere Edda/Gudhrûnarkvidha thridhja',
         'Edda/Ältere Edda/Gudhrûnarkvidha önnur',
         'Edda/Ältere Edda/Hamdismâl',
         'Edda/Ältere Edda/Harbardhsliodh',
         'Edda/Ältere Edda/Helgakvidha Hjörvardhssonar',
         'Edda/Ältere Edda/Helgakvidha Hundingsbana fyrri',
         'Edda/Ältere Edda/Helgakvidha Hundingsbana önnur',
         'Edda/Ältere Edda/Helreidh Brynhildar',
         'Edda/Ältere Edda/Hrafnagaldr Ôdhins',
         'Edda/Ältere Edda/Hyndluliod',
         'Edda/Ältere Edda/Hâvamâl',
         'Edda/Ältere Edda/Hŷmiskvidha',
         'Edda/Ältere Edda/Oddrûnargrâtr',
         'Edda/Ältere Edda/Oegisdrecka',
         'Edda/Ältere Edda/Rîgsmâl',
         'Edda/Ältere Edda/Sigrdrîfumâl',
         'Edda/Ältere Edda/Sigurdharkvidha Fafnisbana fyrsta edha Grîpisspâ',
         'Edda/Ältere Edda/Sigurdharkvidha Fafnisbana thridhja',
         'Edda/Ältere Edda/Sigurdharkvidha Fafnisbana önnur',
         'Edda/Ältere Edda/Sinfiötlalok',
         'Edda/Ältere Edda/Skîrnisför',
         'Edda/Ältere Edda/Thrymskvidha oder Hamarsheimt',
         'Edda/Ältere Edda/Vafthrûdhnismâl',
         'Edda/Ältere Edda/Vegtamskvidha',
         'Edda/Ältere Edda/Völundarkvidha',
         'Edda/Ältere Edda/Völuspâ']

site = pywikibot.Site('de', 'wikisource')
for lemma in sites:
    page = pywikibot.Page(site, lemma)
    page.delete(reason= 'Verschieberest', prompt=False)