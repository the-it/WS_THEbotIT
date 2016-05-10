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
    parser = optparse.OptionParser()
    parser.set_defaults(time=False)
    parser.add_option('--time', action='store_true', dest='time')
    (options, args) = parser.parse_args()

    if len(args) > 4:
        raise ValueError("Zu viele Kommandozeilenargumente.")
    elif len(args) > 0:
        try:
            day = int(args[0])
            month = int(args[1])
            year = int(args[2])
        except:
            raise ValueError("Kommandozeilenargumente sind kein Datum.")

    scanner = CatScan()
    scanner.add_positive_category('Fertig')

    if options.time:
        scanner.last_change_after(year, month, day)
        print('Es werden alle Seiten, die seit dem {}.{}.{} bearbeitet wurden und sich in der Kategorie "Fertig" befinden, dursucht'.format(day, month, year))
    else:
        print('Es werden alle Seiten, die sich in der Kategorie "Fertig" befinden, dursucht')


    lemmas = scanner.run()


    wiki = pywikibot.Site()


if __name__ == "__main__":
    main()