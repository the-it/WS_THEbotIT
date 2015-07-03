__author__ = 'eso'

import requests
import json
import pprint
import time
import datetime
from tools.catscan import CatScan
import pywikibot

if __name__ == "__main__":
    catscan = CatScan()
    catscan.add_positive_categoy("Autoren")
    catscan.add_namespace(0)
    catscan.deactivate_redirects()
    catscan.max_age(48)
    catscan.get_wikidata()
    print(catscan)
    dict = catscan.do()
    pass