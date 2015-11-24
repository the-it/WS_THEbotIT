__author__ = 'eso'

import requests
import json
import pprint
import time
import datetime
import re
from pywikibot import pagegenerators
import pywikibot

if __name__ == "__main__":
    wiki = pywikibot.Site()
    for i in range(10):
        seite = pywikibot.Page(wiki, title='Seite:Loos Sämtliche Schriften.pdf/62', ns=0)
        list_ver = seite.getVersionHistory(reverse=True)
        test = seite.backlinks()
        for i in test:
            print(i)
        print('load the site{}'.format(seite.text))
