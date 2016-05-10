# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
import re
import optparse
import requests
import pywikibot
import time
import json
from tools.catscan.catscan import CatScan


def main():
    first_re = re.compile(r'^\d{3}$')

    parser = optparse.OptionParser()
    parser.set_defaults(time=False)
    parser.add_option('--time', action='store_true', dest='time')
    (options, args) = parser.parse_args()

    if len(args) == 1:
        if first_re.match(args[0]):
            print("Primary argument is : ", args[0])
        else:
            raise ValueError("First argument should be ...")
    elif len(args) > 1:
        raise ValueError("Too many command line arguments")

    if options.time:
        print('debug flag')

    scanner = CatScan()
    scanner.add_positive_category('Fertig')
    scanner.last_change_after(2016, 5, 1)
    lemmas = scanner.run()


    wiki = pywikibot.Site()


if __name__ == "__main__":
    main()