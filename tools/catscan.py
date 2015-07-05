__author__ = 'Erik Sommer'

import datetime
import requests
import json

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

def listify(x):
    """
    If given a non-list, encapsulate in a single-element list.

    @rtype: list
    """
    return x if isinstance(x, list) else [x]

class CatScan:
    """
    Encapsulate the catscan service, written by Markus Manske (http://tools.wmflabs.org/catscan2/catscan2.php).
    It is possible to access all parameters by different setter functions. The function 'run' execute the server inquiry
    with the set parameters. The answer is a list with the matching pages. The inquiry have a timeout by 30 seconds.
    """
    def __init__(self):
        self.header = {'User-Agent': 'Python-urllib/3.1'}
        self.base_address = "http://tools.wmflabs.org/catscan2/catscan2.php"
        self.timeout = 30
        self._options = {}
        self.categories = {"positive": [], "negative": []}
        self.language = "de"
        self.project = "wikisource"

    def __str__(self):
        return self._construct_string()

    def set_language(self, lang):
        self.language = lang

    def set_project(self, proj):
        self.project = proj

    def add_options(self, dict_options):
        self._options.update(dict_options)

    def set_depth(self, depth):
        """
            Defines the search depth for the query.

            :param depth: Count of subcategories that will be searched.
            """
        self.add_options({"depth":depth})

    def add_positive_category(self, category):
        """
        Add category to the positive list
        :param category: string with the category name
        """
        self.categories["positive"].append(category)

    def add_negative_category(self, category):
        self.categories["negative"].append(category)

    def add_namespace(self, namespace):
        # is there a list to process or only a single instance
        namespace = listify(namespace)
        for i in namespace:
            # is there a given integer or the string of a namespace
            if type(i) is int:
                self.add_options({"ns[" + str(i) + "]": "1"})
            else:
                self.add_options({"ns[" + str(namespace_mapping[i]) + "]": "1"})

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

    def _construct_cat_string(self, cat_list):
        cat_string = ""
        i = 0
        for cat in cat_list:
            if i > 0:
                cat_string += ("%0D%0A")
            string_item = cat
            string_item.replace(" ", "+")
            cat_string += string_item
            i += 1
        return cat_string

    def _construct_options(self):
        opt_string = ""
        for key in self._options:
            opt_string += ("&" + key + "=" + str(self._options[key]))
        return opt_string

    def _construct_string(self):
        question_string = self.base_address
        question_string += ("?language=" + self.language)
        question_string += ("&project=" + self.project)
        if len(self.categories["positive"]) != 0:
            question_string += ("&categories=" + (self._construct_cat_string(self.categories["positive"])))
        if len(self.categories["negative"]) != 0:
            question_string += ("&negcats=" + (self._construct_cat_string(self.categories["negative"])))
        if len(self._options) != 0:
            question_string += (self._construct_options())
        question_string += "&format=json&doit=1"
        return question_string

    def run(self):
        try:
            response = requests.get(url=self._construct_string(),
                                    headers=self.header, timeout=self.timeout)
            response_byte = response.content
            response_dict = json.loads(response_byte.decode("utf8"))
            return response_dict['*'][0]['a']['*']
        except Exception as e:
            raise ConnectionError