__author__ = 'Erik Sommer'

import datetime

namespace_mapping = {"Article": 0,
                     "Diskussion": 1,
                     "Benutzer": 2,
                     "Benutzer Diskussion": 3,
                     "Wikisource": 4,
                     "Wikisource Diskussion": 5,
                     "Datei": 6,
                     "Datei Diskussion": 7,
                     "MediaWiki": 8,
                     "MediaWiki Diskussion": 9,
                     "Vorlage": 10,
                     "Vorlage Diskussion": 11,
                     "Hilfe": 12,
                     "Hilfe Diskussion": 13,
                     "Kategorie": 14,
                     "Kategorie Diskussion": 15,
                     "Seite": 102,
                     "Seite Diskussion": 103,
                     "Index": 104,
                     "Index Diskussion": 105,
                     "Modul": 828,
                     "Modul Diskussion": 829,
                     }


class CatScan:
    def __init__(self):
        self.header = {'User-Agent': 'Python-urllib/3.1'}
        self.base_address = "http://tools.wmflabs.org/catscan2/catscan2.php"
        self.timeout = 15
        self.options = {}
        self.categories = {"positive": [], "negative": []}
        self.language = "de"
        self.project = "wikisource"

    def add_options(self, dict_options):
        self.options.update(dict_options)

    def set_depth(self, depth):
        self.options.pop("depth")
        self.add_options({"depth": depth})

    def add_positive_categoy(self, category):
        self.categories["positive"].append(category)

    def add_negative_categoy(self, category):
        self.categories["negative"].append(category)

    def add_namespace(self, namespace):
        # is there a list to process or only a single instance
        if type(namespace) is list:
            for i in namespace:
                # is there a given integer or the string of a namespace
                if type(namespace[i]) is int:
                    self.add_options({"ns[" + str(namespace[i]) + "]": "1"})
                else:
                    self.add_options({"ns[" + str(namespace_mapping[namespace[i]]) + "]": "1"})
        else:
            if type(namespace) is int:
                self.add_options({"ns[" + str(namespace) + "]": "1"})
            else:
                self.add_options({"ns[" + str(namespace_mapping[namespace]) + "]": "1"})

    def activate_redirects(self):
        self.add_options({"show_redirects": "yes"})

    def deactivate_redirects(self):
        self.add_options({"show_redirects": "no"})

    def last_change_before(self, year, month=1, day=1, hour=0, minute=0, second=0):
        last_change = datetime.datetime(year, month, day, hour, minute, second)
        self.add_options({"before": last_change.strftime("%Y%m%d%H%M%S")})

    def last_change_after(self, year, month=1, day=1, hour=0, minute=0, second=0):
        last_change = datetime.datetime(year, month, day, hour, minute, second)
        self.add_options({"after": last_change.strftime("%Y%m%d%H%M%S")})

    def max_age(self, hours):
        self.add_options({"max_age": str(hours)})

    def only_new(self):
        self.add_options({"only_new": "1"})

    def smaller_then(self, file_size):
        self.add_options({"smaller": str(file_size)})

    def larger_then(self, file_size):
        self.add_options({"larger": str(file_size)})

    def get_wikidata(self):
        self.add_options({"get_q": "1"})

    def __construct_cat_string(self, cat_list):
        cat_string = ""
        for i in cat_list:
            if i > 0:
                cat_string.join("%0D%0A")
            string_item = cat_list[i]
            string_item.replace(" ", "+")
            cat_string.join(string_item)
        return cat_string

    def __construct_options(self):
        opt_string = ""
        for key in self.options:
            opt_string.join("&" + key + "=" + self.options[key])
        return opt_string

    def __construct_string(self):
        question_string = self.base_address
        question_string.join("?language=" + self.language)
        question_string.join("&project=" + self.project)
        if len(self.categories["positive"]) != 0:
            question_string.join("&categories=".join(self.__construct_cat_string(self.categories["positive"])))
        if len(self.categories["negative"]) != 0:
            question_string.join("&categories=".join(self.__construct_cat_string(self.categories["negative"])))
        if len(self.options) != 0:
            question_string.join(self.__construct_options())
