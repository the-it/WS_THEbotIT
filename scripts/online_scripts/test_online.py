# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
from tools.catscan import CatScan
import re
import requests
import pywikibot

site = pywikibot.Site('de', 'wikisource')
page = pywikibot.Page(site, title= 'Benutzer:THEbotIT/Test1')
print(page.text)
page.save()