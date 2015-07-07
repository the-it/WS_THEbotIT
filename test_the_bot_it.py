__author__ = 'eso'

import requests
import json
import pprint
import time
import datetime
from tools.catscan import CatScan

if __name__ == "__main__":
    catscan = CatScan()
    catscan.add_positive_category("Autoren")
    catscan.add_namespace(0)
    catscan.deactivate_redirects()
    #catscan.last_change_after(2015,6,16)
    #catscan.last_change_before(2015,6,18)
    catscan.max_age(120)
    catscan.get_wikidata()
    print(catscan)
    t0 = time.time()
    sites = catscan.run()
    print(time.time()-t0)
    t0 = time.time()
    outfile = open("data.json", 'w')
    sites = sites
    json.dump(sites, outfile, ensure_ascii=True)
    print(time.time()-t0)
    del outfile
    outfile = open('data.json', 'r')
    t0 = time.time()
    dict2 = json.load(outfile)
    print(time.time()-t0)
    pass
