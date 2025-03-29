from collections.abc import Mapping
import contextlib
from datetime import datetime
from typing import Generator, Optional, List, cast

from service.ws_re import public_domain
from service.ws_re.template import RE_DATEN, RE_ABSCHNITT, ReDatenException, RE_AUTHOR
from service.ws_re.template._typing import KeyValuePair, ArticleProperties
from service.ws_re.template.property import Property
from service.ws_re.template.re_author import REAuthor
from tools._typing import TemplateParameterDict
from tools.template_finder import TemplateFinder
from tools.template_handler import TemplateHandler, TemplateHandlerException


class Article(Mapping):
    keywords = {
        "BD": "BAND",
        "SS": "SPALTE_START",
        "SE": "SPALTE_END",
        "VG": "VORGÄNGER",
        "NF": "NACHFOLGER",
        "SRT": "SORTIERUNG",
        "KOR": "KORREKTURSTAND",
        "KT": "KURZTEXT",
        "WS": "WIKISOURCE",
        "WP": "WIKIPEDIA",
        "GND": "GND",
        "KSCH": "KEINE_SCHÖPFUNGSHÖHE",
        "TJ": "TODESJAHR",
        "GJ": "GEBURTSJAHR",
        "NT": "NACHTRAG",
        "ÜB": "ÜBERSCHRIFT",
        "VW": "VERWEIS"}

    def __init__(self,
                 article_type: str = RE_DATEN,
                 re_daten_properties: Optional[ArticleProperties] = None,
                 text: str = "",
                 author: REAuthor = REAuthor("")):
        self._article_type = ""
        self.article_type = article_type
        self._text = ""
        self.text = text
        self.author = author
        self._properties = (Property("BAND", ""),
                            Property("SPALTE_START", ""),
                            Property("SPALTE_END", ""),
                            Property("VORGÄNGER", ""),
                            Property("NACHFOLGER", ""),
                            Property("SORTIERUNG", ""),
                            Property("KORREKTURSTAND", ""),
                            Property("KURZTEXT", ""),
                            Property("WIKIPEDIA", ""),
                            Property("WIKISOURCE", ""),
                            Property("GND", ""),
                            Property("KEINE_SCHÖPFUNGSHÖHE", False),
                            Property("TODESJAHR", ""),
                            Property("GEBURTSJAHR", ""),
                            Property("NACHTRAG", False),
                            Property("ÜBERSCHRIFT", False),
                            Property("VERWEIS", False))
        self._init_properties(re_daten_properties)

    def __repr__(self):  # pragma: no cover
        return f"<{self.__class__.__name__} - type:{self._article_type}, author:{self.author}, issue:{self['BAND']}>"

    def __len__(self) -> int:
        return len(self._properties)

    def __iter__(self) -> Generator[Property, None, None]:
        yield from self._properties

    def __getitem__(self, item: str) -> Property:
        for re_property in self._properties:
            if item == re_property.name:
                return re_property
        raise KeyError(f"Key {item} not found in self._properties")

    def __hash__(self):
        return hash(self._article_type) \
            + (hash(self._properties) << 1) \
            + (hash(self._text) << 2) \
            + (hash(self.author) << 3)

    @property
    def article_type(self) -> str:
        return self._article_type

    @article_type.setter
    def article_type(self, new_value: str):
        new_value = new_value.strip()
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
    def common_free(self) -> bool:
        current_year = datetime.now().year
        with contextlib.suppress(ValueError):
            if self["TODESJAHR"].value and \
                    int(self["TODESJAHR"].value) > current_year - public_domain.YEARS_AFTER_DEATH:
                if not self["KEINE_SCHÖPFUNGSHÖHE"].value:
                    return False
            if self["GEBURTSJAHR"].value and int(self["GEBURTSJAHR"].value) > \
                    current_year - public_domain.YEARS_AFTER_BIRTH:
                if not self["KEINE_SCHÖPFUNGSHÖHE"].value:
                    return False
        return True

    def _init_properties(self, properties_dict: Optional[ArticleProperties]):
        if properties_dict:
            for item in properties_dict.items():
                if item[0] in self:
                    try:
                        self[item[0]].value = item[1]
                    except (ValueError, TypeError) as property_error:
                        raise ReDatenException(f"Keypair {item} is not permitted.") \
                            from property_error

    @classmethod
    def from_text(cls, article_text: str) -> 'Article':
        """
        main parser function for initiating a ReArticle from a given piece of text.

        :param article_text: text that represent a valid ReArticle
        """
        finder = TemplateFinder(article_text)
        find_re_daten = finder.get_positions(RE_DATEN)
        find_re_abschnitt = finder.get_positions(RE_ABSCHNITT)
        # only one start template can be present
        if len(find_re_daten) + len(find_re_abschnitt) != 1:
            raise ReDatenException("Article has the wrong structure. There must be one start template")
        if find_re_daten:
            find_re_start = find_re_daten
        else:
            find_re_start = find_re_abschnitt
        find_re_author = finder.get_positions(RE_AUTHOR)
        # only one end template can be present
        if len(find_re_author) != 1:
            raise ReDatenException("Article has the wrong structure. There must one stop template")
        # the templates must have the right order
        if find_re_start[0].start > find_re_author[0].start:
            raise ReDatenException("Article has the wrong structure. Wrong order of templates.")
        # it can only exist text between the start and the end template.
        if find_re_start[0].start != 0:
            raise ReDatenException("Article has the wrong structure. There is text in front of the article.")
        if find_re_author[0].end != len(article_text):
            raise ReDatenException("Article has the wrong structure. There is text after the article.")
        try:
            re_start = TemplateHandler(find_re_start[0].text)
        except TemplateHandlerException as error:
            raise ReDatenException("Start-Template has the wrong structure.") from error
        try:
            re_author = REAuthor.from_template(find_re_author[0].text)
        except TemplateHandlerException as error:
            raise ReDatenException("Author-Template has the wrong structure.") from error
        # cast to KeyValuePair is valid, as all expected arguments in the template should be named
        properties_dict = cls._extract_properties(cast(list[KeyValuePair], re_start.parameters))
        return Article(article_type=re_start.title,
                       re_daten_properties=properties_dict,
                       text=article_text[find_re_start[0].end:find_re_author[0].start]
                       .strip(),
                       author=re_author)

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
            keyword = cls._correct_keyword(template_property)
            properties_dict.update({keyword: template_property["value"]})
        return properties_dict

    @classmethod
    def _correct_keyword(cls, template_property: KeyValuePair) -> str:
        """
        handles slightly different forms of the expected keywords

        Examples: - KSCH -> KEINE_SCHÖPFUNGSHÖHE
                  - keine_schöpfungshöhe -> KEINE_SCHÖPFUNGSHÖHE
                  - SCHÖPFUNGSHÖHE -> KEINE_SCHÖPFUNGSHÖHE

        :param template_property: of parameter extracted by the TemplateHandler.
        :return: correct form of a keyword
        """
        if template_property["key"]:
            keyword = template_property["key"].upper()
            if keyword in cls.keywords:
                keyword = cls.keywords[keyword]
            elif keyword in "".join(cls.keywords.values()):
                for full_keyword in cls.keywords.values():
                    if keyword in full_keyword:
                        keyword = full_keyword
                        break
            else:
                raise ReDatenException(f"REDaten has wrong key word. --> {template_property}")
        else:
            raise ReDatenException(f"REDaten has property without a key word. --> "
                                   f"{template_property}")
        return keyword

    def _get_pre_text(self):
        template_handler = TemplateHandler()
        template_handler.title = RE_DATEN
        list_of_properties: list[TemplateParameterDict] = []
        for re_property in self._properties:
            list_of_properties.append({"key": re_property.name,
                                       "value": re_property.value_to_string()})
        template_handler.update_parameters(list_of_properties)
        return template_handler.get_str(str_complex=True)

    def to_text(self):
        content = []
        if self.article_type == RE_DATEN:
            content.append(self._get_pre_text())
        else:
            content.append(f"{{{{{RE_ABSCHNITT}}}}}")
        content.append(self.text)
        content.append(str(self.author))
        return "\n".join(content)
