import collections
import contextlib
from datetime import datetime
from typing import Union, Tuple, Generator, Optional, Dict, TypedDict, List

from scripts.service.ws_re.template import RE_DATEN, RE_ABSCHNITT, ReDatenException, RE_AUTHOR
from scripts.service.ws_re.template.property import Property, ValueType
from tools.template_finder import TemplateFinder
from tools.template_handler import TemplateHandler, TemplateHandlerException


# type hints
class KeyValuePair(TypedDict):
    key: str
    value: ValueType


ArticleProperties = Dict[str, ValueType]


class Article(collections.MutableMapping):
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
                 re_daten_properties: ArticleProperties = None,
                 text: str = "",
                 author: Tuple[str, str] = ("", "")):
        self._article_type = ""
        self.article_type = article_type
        self._text = ""
        self.text = text
        self._author = ("", "")
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

    def __repr__(self):  # pragma: no cover
        return f"<{self.__class__.__name__} - type:{self._article_type}, author:{self._author}, issue:{self['BAND']}>"

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

    @property
    def common_free(self) -> bool:
        current_year = datetime.now().year
        with contextlib.suppress(ValueError):
            if self["TODESJAHR"].value and int(self["TODESJAHR"].value) > current_year - 71:
                if not self["KEINE_SCHÖPFUNGSHÖHE"].value:
                    return False
            if self["GEBURTSJAHR"].value and int(self["GEBURTSJAHR"].value) > current_year - 171:
                if not self["KEINE_SCHÖPFUNGSHÖHE"].value:
                    return False
        return True

    def __len__(self) -> int:
        return len(self._properties)

    def __iter__(self) -> Generator[Property, None, None]:
        for re_property in self._properties:
            yield re_property

    def __getitem__(self, item: str) -> Property:
        for re_property in self._properties:
            if item == re_property.name:
                return re_property
        raise KeyError(f"Key {item} not found in self._properties")

    def __setitem__(self, key, value):
        pass

    def __delitem__(self, key):
        pass

    def _init_properties(self, properties_dict: Optional[ArticleProperties]):
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
            raise ReDatenException("Article has the wrong structure. There is text in front of the article.")
        if find_re_author[0]["pos"][1] != len(article_text):
            raise ReDatenException("Article has the wrong structure. There is text after the article.")
        try:
            re_start = TemplateHandler(find_re_start[0]["text"])
        except TemplateHandlerException:
            raise ReDatenException("Start-Template has the wrong structure.")
        try:
            re_author = TemplateHandler(find_re_author[0]["text"])
        except TemplateHandlerException:
            raise ReDatenException("Author-Template has the wrong structure.")
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
    def _extract_properties(cls, parameters: List[KeyValuePair]) -> ArticleProperties:
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
