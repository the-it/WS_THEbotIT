# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
from tools.catscan import CatScan
import re
import requests
import pywikibot

site = pywikibot.Site('de', 'wikisource')
page = pywikibot.Page(site, title= 'Seite:OrbisPictus 001.jpg')
print(page.text)