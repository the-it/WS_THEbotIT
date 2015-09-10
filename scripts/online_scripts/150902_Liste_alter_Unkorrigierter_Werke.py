# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
import re
import pywikibot
import datetime
from tools.catscan import CatScan

searcher = CatScan()
searcher.add_positive_category('Werke')
searcher.add_positive_category('Unkorrigiert')
lemmas = searcher.run()


wiki = pywikibot.Site()



