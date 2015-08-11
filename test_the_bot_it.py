__author__ = 'eso'

import requests
import json
import pprint
import time
import datetime
import re
from tools.catscan import CatScan

if __name__ == "__main__":
    for idx, val in enumerate(range(0, 100, 11)):
        print(idx, val)