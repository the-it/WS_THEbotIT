__author__ = 'eso'

import requests
import json
import pprint
import time
import datetime

if __name__ == "__main__":
        last_change = datetime.datetime(2000, 5, 5, 12, 13, 14)
        print(last_change.strftime("%Y%m%d%H%M%S"))
        print(type(str(5)))