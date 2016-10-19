__author__ = 'Erik Sommer'

import datetime
import requests
import json
import re
from urllib.parse import quote
from tools.tools import ToolExeption

namespace_mapping = {"Article": 0,
                     "Diskussion": 1,
                     "Benutzer": 2,
                     "Benutzer Diskussion": 3,
                     "Wikisource": 4,
                     "Wikisource Diskussion": 5,
                     "Wikipedia": 4,
                     "Wikipedia Diskussion": 5,
                     "Wikibooks": 4,
                     "Wikibooks Diskussion": 5,
                     "Wikiquote": 4,
                     "Wikiquote Diskussion": 5,
                     "Wikispecies": 4,
                     "Wikispecies Diskussion": 5,
                     "Wikinews": 4,
                     "Wikinews Diskussion": 5,
                     "Wikionary": 4,
                     "Wikionary Diskussion": 5,
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
                     "Portal": 100,
                     "Portal Diskussion": 101,
                     "Seite": 102,
                     "Seite Diskussion": 103,
                     "Wahl": 102,
                     "Wahl Diskussion": 103,
                     "Meinungen": 102,
                     "Meinungen Diskussion": 103,
                     "Verzeichnis": 102,
                     "Verzeichnis Diskussion": 103,
                     "Index": 104,
                     "Index Diskussion": 105,
                     "Thesaurus": 104,
                     "Thesaurus Diskussion": 105,
                     "Kurs": 106,
                     "Kurs Diskussion": 107,
                     "Reim": 106,
                     "Reim Diskussion": 107,
                     "Projekt": 108,
                     "Projekt Diskussion": 109,
                     "Flexion": 108,
                     "Flexion Diskussion": 109,
                     "Education Program": 446,
                     "Education Program Diskussion": 447,
                     "Modul": 828,
                     "Modul Diskussion": 829,
                     "Gadget ": 2300,
                     "Gadget  Diskussion": 2301,
                     "Gadget-Definition": 2302,
                     "Gadget-Definition Diskussion": 2303,
                     "Thema": 2600}


def listify(x)->list:
    """
    If given a non-list, encapsulate in a single-element list.
    """
    return x if isinstance(x, list) else [x]

class PetScanException(ToolExeption):
    pass


class PetScan:
    """
    Encapsulate the catscan service, written by Markus Manske (https://petscan.wmflabs.org/).
    It is possible to access all parameters by different setter functions. The function 'run' execute the server inquiry
    with the set parameters. The answer is a list with the matching pages. The inquiry have a timeout by 30 seconds.
    """
    def __init__(self):
        self.header = {'User-Agent': 'Python-urllib/3.1'}
        self.base_address = "https://petscan.wmflabs.org/"
        self.timeout = 30
        self.options = {}
        self.categories = {"positive": [], "negative": []}
        self.templates = {'yes': [], 'any': [], 'no': []}
        self.outlinks = {'yes': [], 'any': [], 'no': []}
        self.links_to = {'yes': [], 'any': [], 'no': []}
        self.language = "de"
        self.project = "wikisource"

    def __str__(self):
        return self._construct_string().replace('&format=json&doit=1', '')

    def set_language(self, lang:str):
        self.language = lang

    def set_project(self, proj:str):
        self.project = proj

    def set_timeout(self, sec:int):
        self.timeout = sec

    def add_options(self, dict_options:dict):
        self.options.update(dict_options)

    def set_logic_union(self):
        self.add_options({"combination": "union"})

    def set_search_depth(self, depth: int):
        self.add_options({"depth":depth})

    def add_positive_category(self, category:str, search_depth:int = 1):
        if search_depth > 1:
            category = category + "|{}".format(search_depth)
        self.categories["positive"].append(category)

    def add_negative_category(self, category:str, search_depth:int = 1):
        if search_depth > 1:
            category = category + "|{}".format(search_depth)
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

    def add_yes_template(self, template:str):
        self.templates['yes'].append(template)

    def add_any_template(self, template:str):
        self.templates['any'].append(template)

    def add_no_template(self, template:str):
        self.templates['no'].append(template)

    def add_yes_outlink(self, outlink:str):
        self.outlinks['yes'].append(outlink)

    def add_any_outlink(self, outlink:str):
        self.outlinks['any'].append(outlink)

    def add_no_outlink(self, outlink:str):
        self.outlinks['no'].append(outlink)

    def add_yes_links_to(self, page:str):
        self.links_to['yes'].append(page)

    def add_any_links_to(self, page:str):
        self.links_to['any'].append(page)

    def add_no_links_to(self, page:str):
        self.links_to['no'].append(page)

    def last_change_before(self, year:int, month:int=1, day:int=1, hour:int=0, minute:int=0, second:int=0):
        last_change = datetime.datetime(year, month, day, hour, minute, second)
        self.add_options({"before": last_change.strftime("%Y%m%d%H%M%S")})

    def last_change_after(self, year:int, month:int=1, day:int=1, hour:int=0, minute:int=0, second:int=0):
        last_change = datetime.datetime(year, month, day, hour, minute, second)
        self.add_options({"after": last_change.strftime("%Y%m%d%H%M%S")})

    def max_age(self, hours:int):
        self.add_options({"max_age": str(hours)})

    def only_new(self):
        self.add_options({"only_new": "1"})

    def smaller_then(self, page_size:int):
        self.add_options({"smaller": str(page_size)})

    def larger_then(self, page_size:int):
        self.add_options({"larger": str(page_size)})

    def get_wikidata_items(self):
        self.add_options({"wikidata_item": "any"})

    def get_pages_with_wikidata_items(self):
        self.add_options({"wikidata_item": "with"})

    def get_pages_without_wikidata_items(self):
        self.add_options({"wikidata_item": "without"})

    def set_regex_filter(self, regex:str):
        self.add_options({"regexp_filter": regex})

    def set_last_edit_bots(self, allowed = True):
        self._set_last_edit("bots", allowed)

    def set_last_edit_flagged(self, allowed = True):
        self._set_last_edit("flagged", allowed)

    def set_last_edit_anons(self, allowed = True):
        self._set_last_edit("anons", allowed)

    def _set_last_edit(self, type, allowed):
        if allowed:
            self.add_options({"edits[{}]".format(type): "yes"})
        else:
            self.add_options({"edits[{}]".format(type): "no"})

    sort_criteria = ['title', 'ns_title', 'size', 'date', 'incoming_links', 'random']

    def set_sort_criteria(self, criteria):
        if criteria in self.sort_criteria:
            self.add_options({'sortby': criteria})
        else:
            raise PetScanException("{} isn't a valid sort criteria".format(criteria))

    def set_sortorder_decending(self):
        self.add_options({'sortorder': 'descending'})

    def _construct_list_argument(self, cat_list):
        cat_string = ""
        i = 0
        for cat in cat_list:
            if i > 0:
                cat_string += " \n"
            string_item = cat
            string_item = re.sub(' ', '+', string_item)
            cat_string += string_item
            i += 1
        return cat_string

    def _construct_options(self):
        opt_string = ""
        for key in self.options:
            opt_string += ("&" + key + "=" + str(self.options[key]))
        return opt_string

    def _construct_string(self):
        question_string = [self.base_address]
        question_string.append("?language=" + self.language)
        question_string.append("&project=" + self.project)
        #categories
        if len(self.categories["positive"]) != 0:
            question_string.append("&categories=" + (self._construct_list_argument(self.categories["positive"])))
        if len(self.categories["negative"]) != 0:
            question_string.append("&negcats=" + (self._construct_list_argument(self.categories["negative"])))
        #templates
        if len(self.templates["yes"]) != 0:
            question_string.append("&templates_yes=" + (self._construct_list_argument(self.templates["yes"])))
        if len(self.templates["any"]) != 0:
            question_string.append("&templates_any=" + (self._construct_list_argument(self.templates["any"])))
        if len(self.templates["no"]) != 0:
            question_string.append("&templates_no=" + (self._construct_list_argument(self.templates["no"])))
        #outlinks
        if len(self.outlinks["yes"]) != 0:
            question_string.append("&outlinks_yes=" + (self._construct_list_argument(self.outlinks["yes"])))
        if len(self.outlinks["any"]) != 0:
            question_string.append("&outlinks_any=" + (self._construct_list_argument(self.outlinks["any"])))
        if len(self.outlinks["no"]) != 0:
            question_string.append("&outlinks_no=" + (self._construct_list_argument(self.outlinks["no"])))
        #links_to
        if len(self.links_to["yes"]) != 0:
            question_string.append("&links_to_all=" + (self._construct_list_argument(self.links_to["yes"])))
        if len(self.links_to["any"]) != 0:
            question_string.append("&links_to_any=" + (self._construct_list_argument(self.links_to["any"])))
        if len(self.links_to["no"]) != 0:
            question_string.append("&links_to_no=" + (self._construct_list_argument(self.links_to["no"])))
        #rest of the options
        if len(self.options) != 0:
            question_string.append(self._construct_options())
        question_string.append("&format=json&doit=1")
        return quote("".join(question_string), safe='/&:=?')

    def run(self):
        """
        Execute the search query und returns the results as a list.
        @return: list of result dicionaries.
        @rtype: list
        """
        response = requests.get(url=self._construct_string(),
                                headers=self.header, timeout=self.timeout)
        response_byte = response.content
        response_dict = json.loads(response_byte.decode("utf8"))
        return response_dict['*'][0]['a']['*']