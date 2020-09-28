# pylint: disable=ungrouped-imports
import json
from datetime import datetime
from typing import List, Union
from urllib.parse import quote

import requests

from tools import ToolException
from tools._typing import PetscanLemma


def listify(item) -> list:
    """
    If given a non-list, encapsulate in a single-element list.
    """
    return item if isinstance(item, list) else [item]


class PetScanException(ToolException):
    pass


class PetScan:
    # pylint: disable=too-many-public-methods, too-many-instance-attributes
    """
    Encapsulate the catscan service, written by Markus Manske (https://petscan.wmflabs.org/).
    It is possible to access all parameters by different setter functions.
    The function 'run' execute the server inquiry with the set parameters.
    The answer is a list with the matching pages. The inquiry have a timeout by 30 seconds.
    """

    def __init__(self):
        self.header = {"User-Agent": "Python-urllib/3.1"}
        self.base_address = "https://petscan.wmflabs.org/"
        self._timeout = 30
        self.options = {}
        self.categories = {"positive": [], "negative": []}
        self.templates = {"yes": [], "any": [], "no": []}
        self.outlinks = {"yes": [], "any": [], "no": []}
        self.links_to = {"yes": [], "any": [], "no": []}
        self.language = "de"
        self.project = "wikisource"

    def __str__(self):
        return quote(self._construct_string().replace("&format=json&doit=1", ""), safe="/&:=?")

    def set_language(self, lang: str):
        self.language = lang

    def set_project(self, proj: str):
        self.project = proj

    def set_timeout(self, sec: int):
        self._timeout = sec

    def add_options(self, dict_options: dict):
        self.options.update(dict_options)

    def set_logic_union(self):
        self.add_options({"combination": "union"})

    def set_search_depth(self, depth: int):
        self.add_options({"depth": depth})

    def add_positive_category(self, category: str, search_depth: int = 1):
        if search_depth > 1:
            category = f"{category}|{search_depth}"
        self.categories["positive"].append(category)

    def add_negative_category(self, category: str, search_depth: int = 1):
        if search_depth > 1:
            category = f"{category}|{search_depth}"
        self.categories["negative"].append(category)

    def add_namespace(self, namespace: Union[int, List[int]]):
        # is there a list to process or only a single instance
        namespace = listify(namespace)
        for i in namespace:
            # is there a given integer or the string of a namespace
            self.add_options({"ns[" + str(i) + "]": "1"})

    def activate_redirects(self):
        self.add_options({"show_redirects": "yes"})

    def deactivate_redirects(self):
        self.add_options({"show_redirects": "no"})

    def add_yes_template(self, template: str):
        self.templates["yes"].append(template)

    def add_any_template(self, template: str):
        self.templates["any"].append(template)

    def add_no_template(self, template: str):
        self.templates["no"].append(template)

    def add_yes_outlink(self, outlink: str):
        self.outlinks["yes"].append(outlink)

    def add_any_outlink(self, outlink: str):
        self.outlinks["any"].append(outlink)

    def add_no_outlink(self, outlink: str):
        self.outlinks["no"].append(outlink)

    def add_yes_links_to(self, page: str):
        self.links_to["yes"].append(page)

    def add_any_links_to(self, page: str):
        self.links_to["any"].append(page)

    def add_no_links_to(self, page: str):
        self.links_to["no"].append(page)

    def last_change_before(self, last_change: datetime):
        self.add_options({"before": last_change.strftime("%Y%m%d%H%M%S")})

    def last_change_after(self, last_change: datetime):
        self.add_options({"after": last_change.strftime("%Y%m%d%H%M%S")})

    def max_age(self, hours: int):
        self.add_options({"max_age": str(hours)})

    def only_new(self):
        self.add_options({"only_new": "1"})

    def smaller_then(self, page_size: int):
        self.add_options({"smaller": str(page_size)})

    def larger_then(self, page_size: int):
        self.add_options({"larger": str(page_size)})

    def get_wikidata_items(self):
        self.add_options({"wikidata_item": "any"})

    def get_pages_with_wd_items(self):
        self.add_options({"wikidata_item": "with"})

    def get_pages_without_wd_items(self):
        self.add_options({"wikidata_item": "without"})

    def set_regex_filter(self, regex: str):
        self.add_options({"regexp_filter": regex})

    def set_last_edit_bots(self, allowed=True):
        self._set_last_edit("bots", allowed)

    def set_last_edit_flagged(self, allowed=True):
        self._set_last_edit("flagged", allowed)

    def set_last_edit_anons(self, allowed=True):
        self._set_last_edit("anons", allowed)

    def _set_last_edit(self, type_of_user, allowed):
        if allowed:
            self.add_options({f"edits[{type_of_user}]": "yes"})
        else:
            self.add_options({f"edits[{type_of_user}]": "no"})

    sort_criteria = ["title", "ns_title", "size", "date", "incoming_links", "random"]

    def set_sort_criteria(self, criteria):
        if criteria in self.sort_criteria:
            self.add_options({"sortby": criteria})
        else:
            raise PetScanException(f"{criteria} isn't a valid sort criteria")

    def set_sortorder_decending(self):
        self.add_options({"sortorder": "descending"})

    @staticmethod
    def _construct_list_argument(cat_list):
        string = "\r\n".join(cat_list).replace(" ", "+")
        return string

    def _construct_options(self):
        opt_string = ""
        for key in self.options:
            opt_string += ("&" + key + "=" + str(self.options[key]))
        return opt_string

    def _construct_string(self):
        question_string = list(self.base_address)
        question_string.append("?language=" + self.language)
        question_string.append("&project=" + self.project)
        # categories
        if self.categories["positive"]:
            question_string.append(
                "&categories=" + (self._construct_list_argument(self.categories["positive"])))
        if self.categories["negative"]:
            question_string.append(
                "&negcats=" + (self._construct_list_argument(self.categories["negative"])))
        # templates
        if self.templates["yes"]:
            question_string.append(
                "&templates_yes=" + (self._construct_list_argument(self.templates["yes"])))
        if self.templates["any"]:
            question_string.append(
                "&templates_any=" + (self._construct_list_argument(self.templates["any"])))
        if self.templates["no"]:
            question_string.append(
                "&templates_no=" + (self._construct_list_argument(self.templates["no"])))
        # outlinks
        if self.outlinks["yes"]:
            question_string.append(
                "&outlinks_yes=" + (self._construct_list_argument(self.outlinks["yes"])))
        if self.outlinks["any"]:
            question_string.append(
                "&outlinks_any=" + (self._construct_list_argument(self.outlinks["any"])))
        if self.outlinks["no"]:
            question_string.append(
                "&outlinks_no=" + (self._construct_list_argument(self.outlinks["no"])))
        # links_to
        if self.links_to["yes"]:
            question_string.append(
                "&links_to_all=" + (self._construct_list_argument(self.links_to["yes"])))
        if self.links_to["any"]:
            question_string.append(
                "&links_to_any=" + (self._construct_list_argument(self.links_to["any"])))
        if self.links_to["no"]:
            question_string.append(
                "&links_to_no=" + (self._construct_list_argument(self.links_to["no"])))
        # rest of the options
        if self.options:
            question_string.append(self._construct_options())
        question_string.append("&format=json&doit=1")
        return "".join(question_string)

    def run(self) -> List[PetscanLemma]:
        """
        Execute the search query und returns the results as a list.
        @return: list of result dicionaries.
        @rtype: list
        """
        try:
            response = requests.get(url=self._construct_string(), headers=self.header, timeout=self._timeout)
        except requests.exceptions.RequestException as error:
            raise PetScanException("Get request didn't return correctly") from error
        if response.status_code != 200:
            raise PetScanException("Request wasn't a success")
        response_byte = response.content
        response_dict = json.loads(response_byte.decode("utf8"))
        return response_dict["*"][0]["a"]["*"]  # type: ignore
