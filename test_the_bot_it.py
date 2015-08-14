__author__ = 'eso'

import requests
import json
import pprint
import time
import datetime
import re
from tools.catscan import CatScan
from pywikibot import pagegenerators

if __name__ == "__main__":
    list_of_pages = pagegenerators.AllpagesPageGenerator(namespace=102, content=True)
    pass