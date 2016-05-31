# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')
import optparse
import pywikibot
from tools.catscan.catscan import CatScan
import time


def main():
    start = time.time()
    print("Das Skript wurde um {} gestartet".format(time.strftime('%H:%M:%S (%Y-%m-%d)', time.localtime(start))))
    parser = optparse.OptionParser()
    parser.set_defaults(time=False)
    parser.set_defaults(bots=False)
    parser.add_option('--time', action='store_true', dest='time')
    parser.add_option('--bots', action='store_true', dest='bots')
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

    if options.bots:
        print("Edits von Bots werden berücksichtigt")
    else:
        scanner.set_last_edit_bots(False)
        print("Edits von Bots werden nicht berücksichtigt")

    if options.time:
        scanner.last_change_after(year, month, day)
        print('Es werden alle Seiten, die seit dem {}.{}.{} bearbeitet wurden und sich in der Kategorie "Fertig" befinden, dursucht'.format(day, month, year))
    else:
        print('Es werden alle Seiten, die sich in der Kategorie "Fertig" befinden, dursucht')

    print(scanner)
    lemmas = scanner.run()
    wiki = pywikibot.Site()


    for idx, lemma in enumerate(lemmas):
        if lemma["page_namespace"] == 102:
            lemma_title = "Seite:" + lemma["page_title"]
        else:
            lemma_title = lemma["page_title"]
        page = pywikibot.Page(wiki, lemma_title)

        if not page.protection():
            page.protect(protections = {'move': 'autoconfirmed', 'edit': 'autoconfirmed'}, reason = "".format(lemma_title))
            print("### Lemma {} wurde geschützt. ###".format(lemma_title))
        else:
            print("{}/{}: {}\n{}".format(idx, len(lemmas), lemma_title, page.protection()))
    ende = time.time()
    print("Das Skript hat {} benötigt".format(time.strftime('%H:%M:%S', time.localtime(ende-start))))

if __name__ == "__main__":
    main()