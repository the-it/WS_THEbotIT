import contextlib
import math
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple, Optional, Literal, Pattern, TypedDict, get_args, Union, cast

from service.ws_re.register._base import RegisterException
from service.ws_re.register.authors import Authors
from service.ws_re.register.lemma_chapter import LemmaChapter, ChapterDict
from service.ws_re.volumes import Volume


def _generate_translation_dict():
    _TRANSLATION_DICT_RAW = {"a": "α",
                             "b": "β",
                             "ch": "χ",
                             "d": "δ",
                             "e": "εη",
                             "g": "γ",
                             "i": "jι",
                             "k": "κ",
                             "l": "λ",
                             "m": "μ",
                             "n": "ν",
                             "o": "ωο",  # don't get confused this is an omikron
                             "p": "π",
                             "ph": "φ",
                             "ps": "ψ",
                             "r": "ρ",
                             "s": "σ",
                             "t": "τ",
                             "th": "θ",
                             "u": "vw",
                             "x": "ξ",
                             "y": "υ",
                             "z": "ζ",
                             "": "()?\'ʾʿ–-"}
    _TMP_DICT = {}
    for key in _TRANSLATION_DICT_RAW:  # pylint: disable=consider-using-dict-items
        for character in _TRANSLATION_DICT_RAW[key]:
            _TMP_DICT[character] = key
    return str.maketrans(_TMP_DICT)


def _generate_regex_list(raw_list: List[Tuple[str, str]]) -> List[Tuple[Pattern, str]]:
    regex_list = []
    for regex_pair in raw_list:
        regex_list.append((re.compile(regex_pair[0]), regex_pair[1]))
    return regex_list


def _generate_pre_striping_regex() -> List[Tuple[Pattern, str]]:
    raw = [
        (r"(^| )(?:ἅ)", r"\1ha"),
        (r"(^| )(?:ἑ|ἡ|ἥ)", r"\1he"),
        (r"(^| )(?:ἱ)", r"\1hi"),
        (r"(^| )(?:ὁ|ὅ)", r"\1ho"),
        (r"(^| )(?:ὑ)", r"\1hy"),
    ]
    return _generate_regex_list(raw)


def _generate_pre_translate_regex() -> List[Tuple[Pattern, str]]:
    raw = [
        (r"αυ", "au"),
        (r"ευ", "eu"),
        (r"ου", "u"),
        (r"γγ", "ng"),
    ]
    return _generate_regex_list(raw)


def _generate_pre_finalize_regex() -> List[Tuple[Pattern, str]]:
    raw = [
        # catching of "a ...", "ab ..." and "ad ..."
        (r"^a[db]? ", ""),
        # catching of "X. ..."
        (r"^[a-z]?\. ", ""),
        # unify numbers
        (r"(?<!\d)(\d)(?!\d)", r"00\g<1>"),
        (r"(?<!\d)(\d\d)(?!\d)", r"0\g<1>")
    ]
    return _generate_regex_list(raw)


PRE_ACCENT_STRIPING_REGEX = _generate_pre_striping_regex()
PRE_TRANSLATE_REGEX = _generate_pre_translate_regex()
PRE_FINALIZE_REGEX = _generate_pre_finalize_regex()
TRANSLATION_DICT = _generate_translation_dict()


LemmaKeys = Literal["lemma", "previous", "next", "sort_key", "redirect", "proof_read",
                    "short_description", "wp_link", "ws_link", "wd_link", "no_creative_height", "chapters"]


UpdaterRemoveList = List[str]


class LemmaDict(TypedDict, total=False):
    lemma: str
    previous: str
    next: str
    sort_key: str
    redirect: Union[str, bool]
    proof_read: int
    short_description: str
    wp_link: str
    ws_link: str
    wd_link: str
    no_creative_height: bool
    chapters: List[ChapterDict]


@dataclass(kw_only=True)
class Lemma:
    lemma: str
    previous: Optional[str] = None
    next: Optional[str] = None
    sort_key: Optional[str] = None
    redirect: Optional[Union[str, bool]] = None
    proof_read: Optional[int] = None
    short_description: Optional[str] = None
    wp_link: Optional[str] = None
    ws_link: Optional[str] = None
    wd_link: Optional[str] = None
    no_creative_height: Optional[bool] = None
    chapters: Optional[List[ChapterDict]] = None
    volume: Volume
    authors: Authors

    def __post_init__(self):
        # pylint: disable=attribute-defined-outside-init
        self._chapter_objects: list[LemmaChapter] = []
        self._computed_sort_key: str = ""
        self._recalc_lemma()

    def _recalc_lemma(self):
        if self.chapters:
            self._init_chapters()
        self.set_sort_key()

    def _init_chapters(self):
        # pylint: disable=attribute-defined-outside-init
        self._chapter_objects = []
        with contextlib.suppress(KeyError):
            if self.chapters:
                for chapter in self.chapters:
                    try:
                        self._chapter_objects.append(LemmaChapter.from_dict(chapter))
                    except TypeError as error:
                        raise RegisterException(f"Error init a Lemma chapter from {chapter}") from error

    @property
    def chapter_objects(self) -> List[LemmaChapter]:
        return self._chapter_objects

    def get_sort_key(self) -> str:
        return self._computed_sort_key

    def set_sort_key(self):
        # pylint: disable=attribute-defined-outside-init
        if self.sort_key:
            lemma = self.sort_key
        else:
            lemma = self.lemma
        self._computed_sort_key = self.make_sort_key(lemma)

    @staticmethod
    def _strip_accents(accent_string: str) -> str:
        return ''.join(unicode_char for unicode_char in unicodedata.normalize('NFD', accent_string)
                       if unicodedata.category(unicode_char) != 'Mn')

    @classmethod
    def make_sort_key(cls, lemma: str) -> str:
        lemma = lemma.casefold()
        # handle some things that need regex with accents
        for regex in PRE_ACCENT_STRIPING_REGEX:
            lemma = regex[0].sub(regex[1], lemma)
        # remove all accents
        lemma = cls._strip_accents(lemma)
        # simple replacement of single characters
        for regex in PRE_TRANSLATE_REGEX:
            lemma = regex[0].sub(regex[1], lemma)
        lemma = lemma.translate(TRANSLATION_DICT)
        for regex in PRE_FINALIZE_REGEX:
            lemma = regex[0].sub(regex[1], lemma)
        # delete dots at last
        lemma = lemma.replace(".", " ")
        return lemma.strip()

    def to_dict(self) -> LemmaDict:
        """Convert the lemma object to a dictionary."""
        return_dict: LemmaDict = {}
        valid_keys: tuple[str, ...] = get_args(LemmaKeys)

        for key in valid_keys:
            if key == "lemma":
                if self.lemma:
                    return_dict["lemma"] = self.lemma
            elif key == "chapters":
                if self.chapter_objects:
                    return_dict["chapters"] = self._get_chapter_dicts()
            else:
                value = getattr(self, key)
                if value is not None:
                    return_dict[cast(LemmaKeys, key)] = value

        return return_dict

    @classmethod
    def from_dict(cls, lemma_dict: LemmaDict, volume: Volume, authors: Authors) -> 'Lemma':
        try:
            return Lemma(**lemma_dict, volume=volume, authors=authors)
        except TypeError as error:
            raise RegisterException(f"Error creating a Lemma object from dict {lemma_dict}") from error

    def _get_chapter_dicts(self) -> List[ChapterDict]:
        chapter_list = []
        for chapter in self.chapter_objects:
            chapter_list.append(chapter.to_dict())
        return chapter_list

    def get_table_row(self, print_volume: bool = False, print_author: bool = True) -> str:
        row_string = ["|-"]
        multi_row = ""
        if len(self.chapter_objects) > 1:
            multi_row = f"rowspan={len(self.chapter_objects)}"
        if print_volume:
            row_string.append(f"{multi_row}|{self.volume.name}".strip())
        status = self.status
        if self.chapter_objects:
            for idx, chapter in enumerate(self.chapter_objects):
                row_string.append(self._get_pages(chapter))
                if print_author:
                    row_string.append(self._get_author_str(chapter))
                if idx == 0:
                    row_string.append(f"{multi_row} style=\"background:{status[1]}\"|{status[0]}".strip())
                row_string.append("-")
        else:
            row_string += ["|", "|", f"{multi_row} style=\"background:{status[1]}\"|{status[0]}".strip()]
        # remove the last entry again because the row separator only needed between rows
        if row_string[-1] == "-":
            row_string.pop(-1)
        return "\n|".join(row_string).strip()

    @staticmethod
    def _escape_link_for_templates(link: str) -> str:
        return link.replace("=", "{{=}}")

    def get_link(self) -> str:
        redirect = self.redirect if self.redirect else False
        if redirect:
            link = f"[[RE:{self.lemma}|''{{{{Anker2|{self._escape_link_for_templates(str(self.lemma))}}}}}'']]"
            if isinstance(redirect, str):
                link += f" → '''[[RE:{redirect}|{redirect}]]'''"
        else:
            link = f"[[RE:{self.lemma}|'''{{{{Anker2|{self._escape_link_for_templates(str(self.lemma))}}}}}''']]"
        return link

    def get_wiki_links(self) -> Tuple[str, str]:
        link = ""
        sort_key = ""
        links = []
        sort_keys = []
        if self.wp_link:
            link, sort_key = self._process_wiki_link("wp")
            links.append(link)
            sort_keys.append(sort_key)
        if self.ws_link:
            link, sort_key = self._process_wiki_link("ws")
            links.append(link)
            sort_keys.append(sort_key)
        if self.wd_link:
            links.append(f"[[{self.wd_link}|WD-Item]]")
            sort_keys.append(f"{self.wd_link}")
        if links:
            link = "<br/>".join(links)
            sort_key = f"data-sort-value=\"{sort_keys[0]}\""
        return link, sort_key

    def _process_wiki_link(self, wiki_type: Literal["wp", "ws"]) -> Tuple[str, str]:
        link_type: Literal["ws_link", "wp_link"] = "ws_link"
        if wiki_type == "wp":
            link_type = "wp_link"
        parts = getattr(self, link_type).split(":")
        return f"[[{getattr(self, link_type)}|{self._escape_link_for_templates(parts[-1])}" \
               f"<sup>({wiki_type.upper()} {parts[1]})</sup>]]", \
               f"{parts[0]}:{parts[1]}:{self.make_sort_key(':'.join(parts[2:]))}"

    def _get_start_column(self, lemma_chapter: LemmaChapter) -> int:
        columns_on_page = 4
        if self.volume.name == "R":
            columns_on_page = 2
        return ((math.ceil((lemma_chapter.start + (columns_on_page / 2)) / columns_on_page) - 1) * columns_on_page) + 1

    def _get_pages(self, lemma_chapter: LemmaChapter) -> str:
        pages_str = f"[http://elexikon.ch/RE/{self.volume.name.replace(' ', '')}_" \
                    f"{self._get_start_column(lemma_chapter)}.png {lemma_chapter.start}]"
        if lemma_chapter.end and lemma_chapter.start != lemma_chapter.end:
            pages_str += f"-{lemma_chapter.end}"
        return pages_str

    def _get_author_str(self, lemma_chapter: LemmaChapter) -> str:
        author_str = ""
        if lemma_chapter.author:
            mapped_author = self.authors.get_author_by_mapping(lemma_chapter.author,
                                                               self.volume.name)
            if mapped_author:
                author_str = ", ".join([author.name for author in mapped_author])
            else:
                author_str = lemma_chapter.author
        return author_str

    def get_public_domain_year(self) -> int:
        year = 0
        for chapter in self.chapter_objects:
            if self._get_author_str(chapter):
                mapped_author = None
                if chapter.author:
                    mapped_author = self.authors.get_author_by_mapping(chapter.author, self.volume.name)
                if mapped_author:
                    years = [author.year_public_domain for author in mapped_author if author.year_public_domain]
                    if (tmp_max_year := max(years)) > year:
                        year = tmp_max_year
        return year

    @property
    def status(self) -> Tuple[str, str]:
        unkorrigiert = "#AA0000"
        fertig = "#669966"
        korrigiert = "#556B2F"
        light_red = "#FFCBCB"
        light_yellow = "#9FC859"
        # gray = "#CBCBCB"

        if pd_year := self.get_public_domain_year():
            current_year = datetime.now().year
            if pd_year > current_year:
                if not self.no_creative_height:
                    if self.exists:
                        return str(pd_year), light_yellow
                    return str(pd_year), light_red

        if self.proof_read == 2:
            return "KOR", korrigiert
        if self.proof_read == 3:
            return "FER", fertig

        return "UNK", unkorrigiert

    def update_lemma_dict(self, update_dict: LemmaDict, remove_items: Optional[List[str]] = None):
        """Update lemma attributes from a dictionary."""
        # Update attributes from the dictionary
        for key in update_dict:
            typed_key = cast(LemmaKeys, key)  # Cast to the Literal type for mypy
            setattr(self, typed_key, update_dict[typed_key])

        # Handle items to remove
        if remove_items:
            for key in remove_items:
                typed_key = cast(LemmaKeys, key)  # Cast to the Literal type for mypy
                setattr(self, typed_key, None)

        self._recalc_lemma()

    @property
    def exists(self) -> bool:
        if self.proof_read and self.proof_read > 1:
            return True
        return False
