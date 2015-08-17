__author__ = 'eso'

import requests
import json
import pprint
import time
import datetime
import re
from tools.catscan import CatScan
from pywikibot import pagegenerators
import pywikibot

if __name__ == "__main__":
    wiki = pywikibot.Site()
    for i in range(10):
        seite = pywikibot.Page(wiki, title='THEbotIT/Test{}'.format(i+1), ns=2)
        print('load the site{}'.format(seite.text))
        seite.text = 'test'
        seite.save('test{}'.format(i+1), minor=True, botflag=True)