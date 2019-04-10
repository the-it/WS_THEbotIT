import json
import re
from collections import OrderedDict
from collections.abc import Mapping, Sequence
from enum import Enum
from pathlib import Path
from typing import Union, Generator, Tuple, List

import pywikibot
import roman

from tools.template_handler import TemplateFinder, TemplateFinderException, TemplateHandler

_REGISTER_PATH = Path(__file__).parent.joinpath("register")


class ReDatenException(Exception):
    pass


class Property:
    def __init__(self, name: str, default: Union[str, bool]):
        self._name = name
        self._default = default
        self._value = None

    def _return_by_type(self, value: Union[str, bool]) -> str:
        ret = value
        if not isinstance(self._default, (bool, str)):
            raise TypeError(f"Default value ({self._default}) is invalid")
        if isinstance(self._default, bool):
            if value:
                ret = "ON"
            else:
                ret = "OFF"
        return ret

    @staticmethod
    def _set_bool_by_str(on_off: str) -> bool:
        ret = False
        if on_off in ("ON", "on"):
            return True
        return ret

    @property
    def value(self) -> Union[str, bool]:
        if self._value:
            ret = self._value
        else:
            ret = self._default
        return ret

    @value.setter
    def value(self, new_value: Union[str, bool]):
        if isinstance(new_value, str):
            new_value = new_value.strip()
        if isinstance(new_value, type(self._default)):
            self._value = new_value
        elif new_value in ("ON", "OFF", "", "on", "off") and isinstance(self._default, bool):
            if new_value == "":
                self._value = self._default
            self._value = self._set_bool_by_str(new_value)
        else:
            raise TypeError(f"Value ({new_value}) is not the type "
                            f"of default value ({self._default})")

    @property
    def name(self) -> str:
        return self._name

    def value_to_string(self):
        return self._return_by_type(self.value)

    def __hash__(self):
        return hash(self.name) + hash(self.value)

    def __repr__(self):
        return f"<ReProperty> (name: {self.name}, value: {self.value}, type: {type(self._default)})"


RE_DATEN = "REDaten"
RE_ABSCHNITT = "REAbschnitt"
RE_AUTHOR = "REAutor"


class Article(Mapping):
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
        "KSCH": "KEINE_SCHÖPFUNGSHÖHE",
        "TJ": "TODESJAHR",
        "GJ": "GEBURTSJAHR",
        "NT": "NACHTRAG",
        "ÜB": "ÜBERSCHRIFT",
        "VW": "VERWEIS"}

    def __init__(self,
                 article_type: str = RE_DATEN,
                 re_daten_properties: dict = None,
                 text: str = "",
                 author: Union[Tuple[str, str], str] = ("", "")):
        self._article_type = None
        self.article_type = article_type
        self._text = None
        self.text = text
        self._author = None
        self.author = author
        self._properties = (Property("BAND", ""),
                            Property("SPALTE_START", ""),
                            Property("SPALTE_END", ""),
                            Property("VORGÄNGER", ""),
                            Property("NACHFOLGER", ""),
                            Property("SORTIERUNG", ""),
                            Property("KORREKTURSTAND", ""),
                            Property("WIKIPEDIA", ""),
                            Property("WIKISOURCE", ""),
                            Property("EXTSCAN_START", ""),
                            Property("EXTSCAN_END", ""),
                            Property("GND", ""),
                            Property("KEINE_SCHÖPFUNGSHÖHE", False),
                            Property("TODESJAHR", ""),
                            Property("GEBURTSJAHR", ""),
                            Property("NACHTRAG", False),
                            Property("ÜBERSCHRIFT", False),
                            Property("VERWEIS", False))
        self._init_properties(re_daten_properties)

    @property
    def article_type(self) -> str:
        return self._article_type

    @article_type.setter
    def article_type(self, new_value: str):
        if new_value in (RE_DATEN, RE_ABSCHNITT):
            self._article_type = new_value
        else:
            raise ReDatenException(f"{new_value} is not a permitted article type.")

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, new_value: str):
        if isinstance(new_value, str):
            self._text = new_value
        else:
            raise ReDatenException("Property text must be a string.")

    @property
    def author(self) -> Tuple[str, str]:
        return self._author

    @author.setter
    def author(self, new_value: Union[Tuple[str, str], str]):
        if isinstance(new_value, str):
            self._author = (new_value, "")
        elif isinstance(new_value, tuple) and (len(new_value) == 2) and \
                isinstance(new_value[0], str) and isinstance(new_value[1], str):
            self._author = new_value
        else:
            raise ReDatenException("Property author must be a tuple of strings or one string.")

    def __len__(self) -> int:
        return len(self._properties)

    def __iter__(self) -> Generator[Property, None, None]:
        for re_property in self._properties:
            yield re_property

    def __getitem__(self, item: str):
        for re_property in self._properties:
            if item == re_property.name:
                return re_property
        raise KeyError(f"Key {item} not found in self._properties")

    def _init_properties(self, properties_dict: dict):
        if properties_dict:
            for item in properties_dict.items():
                if item[0] in self:
                    try:
                        self[item[0]].value = item[1]
                    except (ValueError, TypeError) as property_error:
                        raise ReDatenException(f"Keypair {item} is not permitted.") \
                            from property_error

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
        :rtype: Article
        """
        finder = TemplateFinder(article_text)
        find_re_daten = finder.get_positions(RE_DATEN)
        find_re_abschnitt = finder.get_positions(RE_ABSCHNITT)
        # only one start template can be present
        if len(find_re_daten) + len(find_re_abschnitt) != 1:
            raise ReDatenException("Article has the wrong structure. There must one start template")
        if find_re_daten:
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
            raise ReDatenException("Article has the wrong structure. "
                                   "There is text in front of the article.")
        if find_re_author[0]["pos"][1] != len(article_text):
            raise ReDatenException("Article has the wrong structure. "
                                   "There is text after the article.")
        re_start = TemplateHandler(find_re_start[0]["text"])
        re_author = TemplateHandler(find_re_author[0]["text"])
        properties_dict = cls._extract_properties(re_start.parameters)
        author_name = re_author.parameters[0]["value"]
        try:
            author_issue = re_author.parameters[1]["value"]
        except IndexError:
            author_issue = ""
        return Article(article_type=re_start.title,
                       re_daten_properties=properties_dict,
                       text=article_text[find_re_start[0]["pos"][1]:find_re_author[0]["pos"][0]]
                       .strip(),
                       author=(author_name, author_issue))

    @classmethod
    def _extract_properties(cls, parameters: list) -> dict:
        """
        initialise all properties from the template handler to the article dict.
        If a wrong parameter is in the list the function will raise a ReDatenException.

        :param parameters: a list of parameters extracted by the TemplateHandler.
        :return: complete list of extracted parameters
        """
        properties_dict = {}
        #
        for template_property in parameters:
            if template_property["key"]:
                keyword = template_property["key"].upper()
                if keyword in cls.keywords.values():
                    pass
                elif keyword in cls.keywords.keys():
                    keyword = cls.keywords[keyword]
                else:
                    raise ReDatenException(f"REDaten has wrong key word. --> {template_property}")
                properties_dict.update({keyword: template_property["value"]})
            else:
                raise ReDatenException(f"REDaten has property without a key word. --> "
                                       f"{template_property}")
        return properties_dict

    def _get_pre_text(self):
        template_handler = TemplateHandler()
        template_handler.title = RE_DATEN
        list_of_properties = []
        for re_property in self._properties:
            list_of_properties.append({"key": re_property.name,
                                       "value": re_property.value_to_string()})
        template_handler.update_parameters(list_of_properties)
        return template_handler.get_str(str_complex=True)

    def to_text(self):
        content = list()
        if self.article_type == RE_DATEN:
            content.append(self._get_pre_text())
        else:
            content.append(f"{{{{{RE_ABSCHNITT}}}}}")
        content.append(self.text)
        if self.author[0] == "OFF":
            author = f"{{{{{RE_AUTHOR}|{self.author[0]}}}}}"
        elif self.author[1]:
            author = f"{{{{{RE_AUTHOR}|{self.author[0]}|{self.author[1]}}}}}"
        else:
            author = f"{{{{{RE_AUTHOR}|{self.author[0]}}}}}"
        content.append(author)
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
        try:
            re_daten_pos = template_finder.get_positions(RE_DATEN)
            re_abschnitt_pos = template_finder.get_positions(RE_ABSCHNITT)
            re_author_pos = template_finder.get_positions(RE_AUTHOR)
        except TemplateFinderException:
            raise ReDatenException("There are corrupt templates.")
        re_starts = re_daten_pos + re_abschnitt_pos
        re_starts.sort(key=lambda x: x["pos"][0])
        if len(re_starts) != len(re_author_pos):
            raise ReDatenException(
                "The count of start templates doesn't match the count of end templates.")
        # iterate over start and end templates of the articles and create ReArticles of them
        last_handled_char = 0
        for pos_daten, pos_author in zip(re_starts, re_author_pos):
            if last_handled_char < pos_daten["pos"][0]:
                # there is plain text in front of the article
                text_to_handle = self.pre_text[last_handled_char:pos_daten["pos"][0]].strip()
                if text_to_handle:
                    # not just whitespaces
                    self._article_list.append(text_to_handle)
            self._article_list.append(
                Article.from_text(self.pre_text[pos_daten["pos"][0]:pos_author["pos"][1]]))
            last_handled_char = pos_author["pos"][1]
        # handle text after the last complete article
        if last_handled_char < len(self.pre_text):
            self._article_list.append(self.pre_text[last_handled_char:len(self.pre_text)].strip())

    def __getitem__(self, idx: int) -> Union[Article, str]:
        return self._article_list[idx]

    def __len__(self) -> int:
        return len(self._article_list)

    def __delitem__(self, idx: int):
        del self._article_list[idx]

    def __setitem__(self, idx: int, item: Union[Article, str]):
        self._article_list[idx] = item

    def __str__(self) -> str:
        articles = []
        for article in self._article_list:
            if isinstance(article, Article):
                articles.append(article.to_text())
            else:  # it is only a string
                articles.append(article)
        return "\n".join(articles)

    def clean_articles(self):
        new_list = []
        for article in self._article_list:
            if article:
                new_list.append(article)
        self._article_list = new_list

    def has_changed(self) -> bool:
        return self.pre_text != str(self)

    @property
    def is_wirtable(self) -> bool:
        protection_dict = self.page.protection()
        if "edit" in protection_dict.keys():
            if protection_dict["edit"][0] == "sysop":
                return False
        return True

    def save(self, reason: str):
        if self.has_changed():
            self.page.text = str(self)
            if self.is_wirtable:
                try:
                    self.page.save(summary=reason, botflag=True)
                except pywikibot.exceptions.LockedPage:
                    raise ReDatenException(f"Page {self.page.title} is locked, it can't be saved.")
            else:
                raise ReDatenException(f"Page {self.page.title} is protected for normal users, "
                                       f"it can't be saved.")

    def append(self, new_article: Article):
        if isinstance(new_article, Article):
            self._article_list.append(new_article)
        else:
            raise TypeError("You can only append Elements of the type ReArticle")

    def __hash__(self):
        hash_value = 0
        for counter, article in enumerate(self._article_list):
            hash_value += hash(article) << counter
        return hash_value

    @property
    def lemma(self):
        return self.page.title()

    @property
    def splitted_article_list(self) -> List[List[Union[Article, str]]]:
        splitted_list = list()
        for article in self._article_list:
            if isinstance(article, Article) and article.article_type == RE_DATEN:
                splitted_list.append([article])
            else:
                splitted_list[-1].append(article)
        return splitted_list


class VolumeType(Enum):
    FIRST_SERIES = 0
    SECOND_SERIES = 1
    SUPPLEMENTS = 2
    REGISTER = 3


_BASIC_REGEX = r"([IVX]{1,5})"
_REGEX_MAPPING = {VolumeType.FIRST_SERIES: re.compile("^" + _BASIC_REGEX + r"(?:,([1234]))?$"),
                  VolumeType.SECOND_SERIES: re.compile("^" + _BASIC_REGEX + r" A(?:,([12]))?$"),
                  VolumeType.SUPPLEMENTS: re.compile(r"^S " + _BASIC_REGEX + "$"),
                  VolumeType.REGISTER: re.compile(r"^R$")}


class Volume:
    def __init__(self, name: str, year: Union[str, int], start: str = None, end: str = None):
        self._name = name
        self._year = str(year)
        self._start = start
        self._end = end
        self._sortkey = self._compute_sortkey()

    def __repr__(self):  # pragma: no cover
        return f"<VOLUME - name:{self.name}, year:{self.year}, start:{self.start}, " \
               f"end:{self.end}, sort:{self.sort_key}>"

    @property
    def name(self) -> str:
        return self._name

    @property
    def file_name(self) -> str:
        return self.name.replace(",", "_")

    @property
    def year(self):
        return self._year

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    @property
    def type(self):
        for re_volume_type in _REGEX_MAPPING:
            if _REGEX_MAPPING[re_volume_type].match(self.name):
                return re_volume_type
        raise ReDatenException(f"Name of Volume {self.name} is malformed.")

    def _compute_sortkey(self):
        match = _REGEX_MAPPING[self.type].search(self.name)
        key = "4"
        latin_number = 0
        if self.name != "R":
            latin_number = roman.fromRoman(match.group(1))
        if self.type == VolumeType.FIRST_SERIES:
            key = f"1_{latin_number:02d}_{match.group(2)}"
        elif self.type == VolumeType.SECOND_SERIES:
            key = f"2_{latin_number:02d}_{match.group(2)}"
        elif self.type == VolumeType.SUPPLEMENTS:
            key = f"3_{latin_number:02d}"
        return key

    @property
    def sort_key(self) -> str:
        return self._sortkey


class Volumes(Mapping):
    def __init__(self):
        path_to_file = Path(__file__).parent.joinpath("volumes.json")
        with open(str(path_to_file), encoding="utf-8") as json_file:
            _volume_list = json.load(json_file)
        _volume_mapping = OrderedDict()
        for item in _volume_list:
            _volume_mapping[item["name"]] = Volume(**item)
        self._volume_mapping = _volume_mapping

    def __getitem__(self, item: str) -> Volume:
        try:
            return self._volume_mapping[item]
        except KeyError:
            raise ReDatenException(f"Register {item} doesn't exists")

    def __len__(self) -> int:
        return len(self._volume_mapping.keys())

    def __iter__(self) -> str:
        for key in self._volume_mapping:
            yield key

    def special_volume_iterator(self, volume_type: VolumeType) -> Generator[Volume, None, None]:
        for volume_key in self:
            volume = self[volume_key]
            if volume.type == volume_type:
                yield volume

    @property
    def first_series(self) -> Generator[Volume, None, None]:
        for volume in self.special_volume_iterator(VolumeType.FIRST_SERIES):
            yield volume

    @property
    def second_series(self) -> Generator[Volume, None, None]:
        for volume in self.special_volume_iterator(VolumeType.SECOND_SERIES):
            yield volume

    @property
    def supplements(self) -> Generator[Volume, None, None]:
        for volume in self.special_volume_iterator(VolumeType.SUPPLEMENTS):
            yield volume

    @property
    def register(self) -> Generator[Volume, None, None]:
        for volume in self.special_volume_iterator(VolumeType.REGISTER):
            yield volume

    @property
    def all_volumes(self) -> Generator[Volume, None, None]:
        for volume_key in self:
            yield self[volume_key]
