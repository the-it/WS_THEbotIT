from collections import Mapping
from collections.abc import Sequence
from typing import Union

from pywikibot import Page

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
        else:
            raise TypeError("Value ({}) is not the type of default value ({})".format(new_value, self._default))

    @property
    def name(self):
        return self._name

    def __str__(self):
        return self._return_by_type(self.value)

    def __hash__(self):
        return hash(self.name) + hash(self.value)


class ReArticle(Mapping):
    def __init__(self, article_type: str="REDaten", re_daten_properties: dict=None, text: str="", author: str=""):
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
                            ReProperty("KORREKTURSTATUS", ""),
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
        if new_value in ("REDaten", "REAbschnitt"):
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
        find_re_daten = finder.get_positions("REDaten")
        find_re_abschnitt = finder.get_positions("REAbschnitt")
        # only one start template can be present
        if len(find_re_daten) + len(find_re_abschnitt) != 1:
            raise ReDatenException("Article has the wrong structure. There must one start template")
        if len(find_re_daten):
            find_re_start = find_re_daten
        else:
            find_re_start = find_re_abschnitt
        find_re_author = finder.get_positions("REAutor")
        # only one end template can be present
        if len(find_re_author) != 1:
            raise ReDatenException("Article has the wrong structure. There must one stop template")
        # the templates must have the right order
        if find_re_start[0]["pos"][0] > find_re_author[0]["pos"][0]:
            raise ReDatenException("Article has the wrong structure. Wrong order of templates.")
        re_start = TemplateHandler(find_re_start[0]["text"])
        re_author = TemplateHandler(find_re_author[0]["text"])
        properties_dict = {}
        # initialise all properties from the template handler to the article dict
        for template_property in re_start.parameters:
            if template_property["key"]:
                properties_dict.update({template_property["key"]: template_property["value"]})
            else:
                raise ReDatenException("REDaten has property without a key word. --> {}".format(template_property))
        return ReArticle(article_type=re_start.title,
                         re_daten_properties=properties_dict,
                         text=article_text[find_re_start[0]["pos"][1]:find_re_author[0]["pos"][0]],
                         author=re_author.parameters[0]["value"][0:-1])  # last character is every time a point


class RePage(Sequence):
    def __init__(self, wiki_page: Page):
        self.page = wiki_page
        self.pre_text = self.page.text
        self.page_dict = list()

        self._init_page_dict()

    def _init_page_dict(self):
        template_finder = TemplateFinder(self.pre_text)
        re_daten_pos = template_finder.get_positions("REDaten")
        re_autor_pos = template_finder.get_positions("REAutor")

    def __getitem__(self, item):
        pass

    def __len__(self):
        pass