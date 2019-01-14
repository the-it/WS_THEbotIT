from collections import OrderedDict
from collections.abc import Mapping, Sequence
from enum import Enum
from pathlib import Path
import re
from typing import Union, Generator, Tuple, Dict

import pywikibot
import yaml

from tools.template_handler import TemplateFinder, TemplateFinderException, TemplateHandler


class ReDatenException(Exception):
    pass


class ReProperty():
    def __init__(self, name: str, default: Union[str, bool]):
        self._name = name
        self._default = default
        self._value = None

    def _return_by_type(self, value: Union[str, bool]) -> str:
        ret = value
        if not isinstance(self._default, (bool, str)):
            raise TypeError("Default value ({}) is invalid".format(self._default))
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
            raise TypeError("Value ({}) is not the type of default value ({})"
                            .format(new_value, self._default))

    @property
    def name(self) -> str:
        return self._name

    def value_to_string(self):
        return self._return_by_type(self.value)

    def __hash__(self):
        return hash(self.name) + hash(self.value)

    def __repr__(self):
        return "<ReProperty> (name: {}, value: {}, type: {})"\
            .format(self.name, self.value, type(self._default))


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
                            ReProperty("GEBURTSJAHR", ""),
                            ReProperty("NACHTRAG", False),
                            ReProperty("ÜBERSCHRIFT", False),
                            ReProperty("VERWEIS", False))
        self._init_properties(re_daten_properties)

    @property
    def article_type(self) -> str:
        return self._article_type

    @article_type.setter
    def article_type(self, new_value: str):
        if new_value in (RE_DATEN, RE_ABSCHNITT):
            self._article_type = new_value
        else:
            raise ReDatenException("{} is not a permitted article type.".format(new_value))

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

    def __iter__(self) -> Generator[ReProperty, None, None]:
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
                    try:
                        self[item[0]].value = item[1]
                    except (ValueError, TypeError) as property_error:
                        raise ReDatenException(
                            "Keypair {} is not permitted.".format(item)) from property_error

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
        return ReArticle(article_type=re_start.title,
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
                    raise ReDatenException("REDaten has wrong key word. --> {}"
                                           .format(template_property))
                properties_dict.update({keyword: template_property["value"]})
            else:
                raise ReDatenException("REDaten has property without a key word. --> {}"
                                       .format(template_property))
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
            content.append("{{{{{}}}}}".format(RE_ABSCHNITT))
        content.append(self.text)
        if self.author[0] == "OFF":
            author = "{{{{{}|{}}}}}".format(RE_AUTHOR, self.author[0])
        elif self.author[1]:
            author = "{{{{{}|{}|{}}}}}".format(RE_AUTHOR, self.author[0], self.author[1])
        else:
            author = "{{{{{}|{}}}}}".format(RE_AUTHOR, self.author[0])
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
                ReArticle.from_text(self.pre_text[pos_daten["pos"][0]:pos_author["pos"][1]]))
            last_handled_char = pos_author["pos"][1]
        # handle text after the last complete article
        if last_handled_char < len(self.pre_text):
            self._article_list.append(self.pre_text[last_handled_char:len(self.pre_text)].strip())

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
                    raise ReDatenException("Page {} is locked, it can't be saved."
                                           .format(self.page.title))
            else:
                raise ReDatenException("Page {} is protected for normal users, it can't be saved."
                                       .format(self.page.title))

    def append(self, new_article: ReArticle):
        if isinstance(new_article, ReArticle):
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


class ReVolumeType(Enum):
    FIRST_SERIES = 0
    SECOND_SERIES = 1
    SUPPLEMENTS = 2
    REGISTER = 3


_BASIC_REGEX = r"[IVX]{1,5}"
_REGEX_MAPPING = {ReVolumeType.FIRST_SERIES: re.compile("^" + _BASIC_REGEX + r"(?:,[1234])?$"),
                  ReVolumeType.SECOND_SERIES: re.compile("^" + _BASIC_REGEX + r" A(?:,[12])?$"),
                  ReVolumeType.SUPPLEMENTS: re.compile(r"^S " + _BASIC_REGEX + "$"),
                  ReVolumeType.REGISTER: re.compile(r"^R$")}


class ReVolume():
    def __init__(self, name: str, year: Union[str, int], start: str = None, end: str = None):
        self._name = name
        self._year = str(year)
        self._start = start
        self._end = end

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
        raise ReDatenException("Name of Volume {} is malformed.".format(self.name))


class ReVolumes(Mapping):
    def __init__(self):
        path_to_file = Path(__file__).parent.joinpath("volumes.yaml")
        with open(str(path_to_file), encoding="utf-8") as yaml_file:
            _volume_list = yaml.safe_load(yaml_file.read())
        _volume_mapping = OrderedDict()
        for item in _volume_list:
            _volume_mapping[item["name"]] = ReVolume(**item)
        self._volume_mapping = _volume_mapping

    def __getitem__(self, item: str) -> ReVolume:
        try:
            return self._volume_mapping[item]
        except ValueError:
            raise ReDatenException("Register {} doesn't exists".format(item))

    def __len__(self) -> int:
        return len(self._volume_mapping.keys())

    def __iter__(self) -> str:
        for key in self._volume_mapping:
            yield key

    def special_volume_iterator(self, volume_type: ReVolumeType) -> Generator[ReVolume, None, None]:
        for volume_key in self:
            volume = self[volume_key]
            if volume.type == volume_type:
                yield volume

    @property
    def first_series(self) -> Generator[ReVolume, None, None]:
        for volume in self.special_volume_iterator(ReVolumeType.FIRST_SERIES):
            yield volume

    @property
    def second_series(self) -> Generator[ReVolume, None, None]:
        for volume in self.special_volume_iterator(ReVolumeType.SECOND_SERIES):
            yield volume

    @property
    def supplements(self) -> Generator[ReVolume, None, None]:
        for volume in self.special_volume_iterator(ReVolumeType.SUPPLEMENTS):
            yield volume

    @property
    def register(self) -> Generator[ReVolume, None, None]:
        for volume in self.special_volume_iterator(ReVolumeType.REGISTER):
            yield volume

    @property
    def all_volumes(self) -> Generator[ReVolume, None, None]:
        for volume_key in self:
            yield self[volume_key]


class ReRegisterLemma(Mapping):
    def __init__(self, lemma_dict: Dict[str, Union[str, list]], issue: str):
        self._lemma_dict = lemma_dict
        self.issue = ReVolumes()[issue]
        if not self.is_valid():
            raise ReDatenException("Error init RegisterLemma. Key missing in {}"
                                   .format(self._lemma_dict))

    def __getitem__(self, item):
        try:
            return self._lemma_dict[item]
        except KeyError:
            return None

    def __iter__(self):
        return iter(self._lemma_dict)

    def __len__(self):
        return len(self._lemma_dict)

    def keys(self):
        return self._lemma_dict.keys()

    def is_valid(self) -> bool:
        if "lemma" not in self.keys() \
                or "chapters" not in self.keys():
            return False
        return True

    def get_old_table_row(self) -> str:
        return ""

    def _get_link(self) -> str:
        return "[[RE:{lemma}]]{{{{Anker|{lemma}}}}}".format(lemma=self["lemma"])


class ReRegisterAuthors:
    def __init__(self):
        pass