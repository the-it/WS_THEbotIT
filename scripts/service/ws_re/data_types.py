from collections import Mapping
from collections.abc import Sequence
from typing import Union

import pywikibot

from tools.template_handler import TemplateFinder, TemplateHandler


class ReDatenException(Exception):
    pass


class ReProperty(object):
    def __init__(self, name, default):
        self._name = name
        self._default = default
        self._value = None

    def _return_by_type(self, value):
        if isinstance(self._default, bool):
            if value:
                return "ON"
            else:
                return "OFF"
        elif isinstance(self._default, str):
            return value
        else:
            raise TypeError("Default value ({}) is invalid".format(self._default))

    def _set_bool_by_str(self, on_off: str):
        if on_off == "ON":
            return True
        else:
            return False

    @property
    def value(self):
        if self._value:
            return self._value
        else:
            return self._default

    @value.setter
    def value(self, new_value: Union[str, bool]):
        if isinstance(new_value, type(self._default)):
            self._value = new_value
        elif new_value in ("ON", "OFF") and type(self._default) == bool:
            self._value = self._set_bool_by_str(new_value)
        else:
            raise TypeError("Value ({}) is not the type of default value ({})".format(new_value, self._default))

    @property
    def name(self):
        return self._name

    def __str__(self):
        return self._return_by_type(self.value)

    def __hash__(self):
        return hash(self.name) + hash(self.value)

RE_DATEN = "REDaten"
RE_ABSCHNITT = "REAbschnitt"
RE_AUTHOR = "REAutor"


class ReArticle(Mapping):
    keywords = {
        "BD": "BAND",
        "SS": "SPALTE_START",
        "SE": "SPALTE_END",
        "VG": "VORGÄNGER",
        "NF": "NACHFOLGER",
        "SRT": "SORTIERUNG",
        "KOR": "KORREKTURSTAND",
        "WS": "WIKISOURCE",
        "WP": "WIKIPEDIA",
        "XS": "EXTSCAN_START",
        "XE": "EXTSCAN_END",
        "GND": "GND",
        "SCH": "KEINE_SCHÖPFUNGSHÖHE",
        "TJ": "TODESJAHR",
        "ÜB": "ÜBERSCHRIFT",
        "VW": "VERWEIS",
        "NT": "NACHTRAG"}

    def __init__(self, article_type: str=RE_DATEN, re_daten_properties: dict=None, text: str="", author: str=""):
        self._article_type = None
        self.article_type = article_type
        self._text = None
        self.text = text
        self._author = None
        self.author = author
        self._properties = (ReProperty("BAND", ""),
                            ReProperty("SPALTE_START", ""),
                            ReProperty("SPALTE_END", ""),
                            ReProperty("VORGÄNGER", ""),
                            ReProperty("NACHFOLGER", ""),
                            ReProperty("SORTIERUNG", ""),
                            ReProperty("KORREKTURSTAND", ""),
                            ReProperty("WIKIPEDIA", ""),
                            ReProperty("WIKISOURCE", ""),
                            ReProperty("EXTSCAN_START", ""),
                            ReProperty("EXTSCAN_END", ""),
                            ReProperty("GND", ""),
                            ReProperty("KEINE_SCHÖPFUNGSHÖHE", False),
                            ReProperty("TODESJAHR", ""),
                            ReProperty("ÜBERSCHRIFT", False),
                            ReProperty("VERWEIS", False),
                            ReProperty("NACHTRAG", False))
        self._init_properties(re_daten_properties)

    @property
    def article_type(self):
        return self._article_type

    @article_type.setter
    def article_type(self, new_value: str):
        if new_value in (RE_DATEN, RE_ABSCHNITT):
            self._article_type = new_value
        else:
            raise ReDatenException("{} is not a permitted article type.".format(new_value))

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, new_value: str):
        if isinstance(new_value, str):
            self._text = new_value
        else:
            raise ReDatenException("Property text must be a string.")

    @property
    def author(self):
        return self._author

    @author.setter
    def author(self, new_value: str):
        if isinstance(new_value, str):
            self._author = new_value
        else:
            raise ReDatenException("Property author must be a string.")

    def __len__(self):
        return len(self._properties)

    def __iter__(self):
        for re_property in self._properties:
            yield re_property

    def __getitem__(self, item: str):
        for re_property in self._properties:
            if item == re_property.name:
                return re_property
        raise KeyError("Key {} not found in self._properties".format(item))

    def _init_properties(self, properties_dict: dict):
        if properties_dict:
            for item in properties_dict.items():
                if item[0] in self:
                    self[item[0]].value = item[1]

    def __hash__(self):
        return hash(self._article_type) \
               + (hash(self._properties) << 1) \
               + (hash(self._text) << 2) \
               + (hash(self._author) << 3)

    @classmethod
    def from_text(cls, article_text):
        """
        main parser function for initiating a ReArticle from a given piece of text.

        :param article_text: text that represent a valid ReArticle
        :rtype: ReArticle
        """
        finder = TemplateFinder(article_text)
        find_re_daten = finder.get_positions(RE_DATEN)
        find_re_abschnitt = finder.get_positions(RE_ABSCHNITT)
        # only one start template can be present
        if len(find_re_daten) + len(find_re_abschnitt) != 1:
            raise ReDatenException("Article has the wrong structure. There must one start template")
        if len(find_re_daten):
            find_re_start = find_re_daten
        else:
            find_re_start = find_re_abschnitt
        find_re_author = finder.get_positions(RE_AUTHOR)
        # only one end template can be present
        if len(find_re_author) != 1:
            raise ReDatenException("Article has the wrong structure. There must one stop template")
        # the templates must have the right order
        if find_re_start[0]["pos"][0] > find_re_author[0]["pos"][0]:
            raise ReDatenException("Article has the wrong structure. Wrong order of templates.")
        # it can only exists text between the start and the end template.
        if find_re_start[0]["pos"][0] != 0:
            raise ReDatenException("Article has the wrong structure. There is text in front of the article.")
        if find_re_author[0]["pos"][1] != len(article_text):
            raise ReDatenException("Article has the wrong structure. There is text after the article.")
        re_start = TemplateHandler(find_re_start[0]["text"])
        re_author = TemplateHandler(find_re_author[0]["text"])
        properties_dict = cls._extract_properties(re_start.parameters)
        return ReArticle(article_type=re_start.title,
                         re_daten_properties=properties_dict,
                         text=article_text[find_re_start[0]["pos"][1]:find_re_author[0]["pos"][0]].strip(),
                         author=re_author.parameters[0]["value"][0:-1])  # last character is every time a point

    @classmethod
    def _extract_properties(cls, parameters: list) -> dict:
        """
        initialise all properties from the template handler to the article dict. If a wrong parameter is in the list
        the function will raise a ReDatenException.

        :param parameters: a list of parameters extracted by the TemplateHandler.
        :return: complete list of extracted parameters
        """
        properties_dict = {}
        #
        for template_property in parameters:
            if template_property["key"]:
                keyword = template_property["key"]
                if keyword in cls.keywords.values():
                    pass
                elif keyword in cls.keywords.keys():
                    keyword = cls.keywords[keyword]
                else:
                    raise ReDatenException("REDaten has wrong key word. --> {}".format(template_property))
                properties_dict.update({keyword: template_property["value"]})
            else:
                raise ReDatenException("REDaten has property without a key word. --> {}".format(template_property))
        return properties_dict

    def _get_pre_text(self):
        template_handler = TemplateHandler()
        template_handler.title = RE_DATEN
        list_of_properties = []
        for re_property in self._properties:
            list_of_properties.append({"key": re_property.name, "value": str(re_property)})
        template_handler.update_parameters(list_of_properties)
        return template_handler.get_str(str_complex=True)

    def to_text(self):
        content = list()
        if self.article_type == RE_DATEN:
            content.append(self._get_pre_text())
        else:
            content.append("{{{{{}}}}}".format(RE_ABSCHNITT))
        content.append(self.text)
        content.append("{{{{{}|{}.}}}}".format(RE_AUTHOR, self.author))
        return "\n".join(content)


class RePage(Sequence):
    def __init__(self, wiki_page: pywikibot.Page):
        self.page = wiki_page
        self.pre_text = self.page.text
        self._article_list = list()

        self._init_page_dict()

    def _init_page_dict(self):
        # find the positions of all key templates
        template_finder = TemplateFinder(self.pre_text)
        re_daten_pos = template_finder.get_positions(RE_DATEN)
        re_abschnitt_pos = template_finder.get_positions(RE_ABSCHNITT)
        re_author_pos = template_finder.get_positions(RE_AUTHOR)
        re_starts = re_daten_pos + re_abschnitt_pos
        re_starts.sort(key=lambda x: x["pos"][0])
        if len(re_starts) != len(re_author_pos):
            raise ReDatenException("The count of start templates doesn't match the count of end templates.")
        # iterate over start and end templates of the articles and create ReArticles of them
        last_handled_char = 0
        for pos_daten, pos_author in zip(re_starts, re_author_pos):
            if last_handled_char < pos_daten["pos"][0]:
                # there is plain text in front of the article
                text_to_handle = self.pre_text[last_handled_char:pos_daten["pos"][0]].strip()
                if text_to_handle:
                    # not just whitespaces
                    self._article_list.append(text_to_handle)
            self._article_list.append(ReArticle.from_text(self.pre_text[pos_daten["pos"][0]:pos_author["pos"][1]]))
            last_handled_char = pos_author["pos"][1]
        # handle text after the last complete article
        if last_handled_char < len(self.pre_text):
            self._article_list.append(self.pre_text[last_handled_char:len(self.pre_text)])

    def __getitem__(self, item: int) -> ReArticle:
        return self._article_list[item]

    def __len__(self) -> int:
        return len(self._article_list)

    def __str__(self) -> str:
        articles = []
        for article in self._article_list:
            if isinstance(article, ReArticle):
                articles.append(article.to_text())
            else:  # it is only a string
                articles.append(article)
        return "\n".join(articles)

    def save(self, reason: str):
        if self.pre_text != str(self):
            self.page.text = str(self)
            self.page.save(summary=reason, botflag=True)
