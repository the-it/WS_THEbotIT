__author__ = 'Erik Sommer'

import time

namespace_mapping = {"Article":0,
                     "Diskussion":1,
                     "Benutzer":2,
                     "Benutzer Diskussion":3,
                     "Wikisource":4,
                     "Wikisource Diskussion":5,
                     "Datei":6,
                     "Datei Diskussion":7,
                     "MediaWiki":8,
                     "MediaWiki Diskussion":9,
                     "Vorlage":10,
                     "Vorlage Diskussion":11,
                     "Hilfe":12,
                     "Hilfe Diskussion":13,
                     "Kategorie":14,
                     "Kategorie Diskussion":15,
                     "Seite":102,
                     "Seite Diskussion":103,
                     "Index":104,
                     "Index Diskussion":105,
                     "Modul":828,
                     "Modul Diskussion":829,
                     }


class CatScan:
    def __init__(self):
        self.header = {'User-Agent':'Python-urllib/3.1'}
        self.base_address = "http://tools.wmflabs.org/catscan2/catscan2.php"
        self.timeout = 15
        self.options = {}
        self.namespace = {0}
        self.categories = {"positive":[], "negative":[]}
        self.language = "de"
        self.project = "ws"

    def add_options(self, dict_options):
        self.options.update(dict_options)

    def set_depth(self, depth):
        self.options.pop("depth")
        self.add_options({"depth":depth})

    def add_positive_categoy(self, category):
        self.categories["positive"].append(category)

    def add_negative_categoy(self, category):
        self.categories["negative"].append(category)
        self.namespace.remove()

    def add_namespace(self, namespace):
        # is there a list to process or only a single instance
        if type(namespace) is list:
            for i in namespace:
                # is there a given integer or the string of a namespace
                if type(namespace[i]) is int:
                    self.namespace.add(namespace[i])
                else:
                    self.namespace.add(namespace_mapping[namespace[i]])
        else:
            if type(namespace) is int:
                self.namespace.add(namespace)
            else:
                self.namespace.add(namespace_mapping[namespace])

    def activate_redirects(self):
        self.add_options({"show_redirects": "yes"})

    def deactivate_redirects(self):
        self.add_options({"show_redirects": "no"})

    def last_change_before(self):
        now = time()
        now = time.strftime()


http://tools.wmflabs.org/catscan2/catscan2.php?language=de&project=wikisource&categories=Autoren&show_redirects=yes&before=20001212012244&max_age=120&only_new=1