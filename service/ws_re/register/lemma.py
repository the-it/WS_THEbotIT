import contextlib
import re
import unicodedata
from datetime import datetime
from typing import List, Tuple, KeysView, Optional, Literal, Pattern

from service.ws_re.register._base import RegisterException
from service.ws_re.register._typing import ChapterDict, LemmaDictKeys, LemmaDictItems, LemmaDict
from service.ws_re.register.authors import Authors
from service.ws_re.register.lemma_chapter import LemmaChapter
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
    for key in _TRANSLATION_DICT_RAW:
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


class Lemma():
    _keys = ["lemma", "previous", "next", "sort_key", "redirect", "proof_read", "wp_link", "ws_link", "wd_link",
             "chapters"]

    def __init__(self,
                 lemma_dict: LemmaDict,
                 volume: Volume,
                 authors: Authors):
        self._lemma_dict: LemmaDict = lemma_dict
        self._authors: Authors = authors
        self._volume = volume
        self._chapters: List[LemmaChapter] = []
        self._sort_key = ""
        self._recalc_lemma()

    def _recalc_lemma(self):
        if "chapters" in self._lemma_dict and self._lemma_dict["chapters"]:
            self._init_chapters()
        self._set_sort_key()

    def _init_chapters(self):
        self._chapters = []
        with contextlib.suppress(KeyError):
            for chapter in self._lemma_dict["chapters"]:
                self._chapters.append(LemmaChapter(chapter))
        if not self.is_valid():
            raise RegisterException(f"Error init RegisterLemma. Key missing in {self._lemma_dict}")

    def __repr__(self):  # pragma: no cover
        return f"<{self.__class__.__name__} - lemma:{self['lemma']}, previous:{self['previous']}, " \
               f"next:{self['next']}, chapters:{len(self._chapters)}, volume:{self._volume.name}>"

    def __getitem__(self, item: LemmaDictKeys) -> Optional[LemmaDictItems]:
        try:
            return self._lemma_dict[item]
        except KeyError:
            return None

    def __len__(self):
        return len(self._lemma_dict)

    def __iter__(self):
        return iter(self._lemma_dict)

    @property
    def volume(self) -> Volume:
        return self._volume

    @property
    def chapters(self) -> List[LemmaChapter]:
        return self._chapters

    @property
    def sort_key(self) -> str:
        return self._sort_key

    def _set_sort_key(self):
        if self["sort_key"]:
            lemma = self["sort_key"]
        else:
            lemma = self["lemma"]
        self._sort_key = self.make_sort_key(lemma)

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

    def keys(self) -> KeysView[str]:
        return self._lemma_dict.keys()  # type: ignore  # mypy don't get that TypedDicts are Dicts?

    @property
    def lemma_dict(self) -> LemmaDict:
        return_dict: LemmaDict = {}
        for property_key in self._keys:
            if property_key in self.keys():
                if property_key == "chapters":
                    value = self._get_chapter_dicts()
                else:
                    value = self._lemma_dict[property_key]  # type: ignore # TypedDict only works with string literals
                if value:
                    return_dict[property_key] = value  # type: ignore # TypedDict only works with string literals
        return return_dict

    def _get_chapter_dicts(self) -> List[ChapterDict]:
        chapter_list = []
        for chapter in self.chapters:
            chapter_list.append(chapter.get_dict())
        return chapter_list

    def is_valid(self) -> bool:
        if "lemma" not in self.keys():
            return False
        if self._chapters:
            for chapter in self._chapters:
                if not chapter.is_valid():
                    return False
        return True

    def get_table_row(self, print_volume: bool = False) -> str:
        row_string = ["|-"]
        interwiki_links, interwiki_sort_key = self.get_wiki_links()
        proof_color, proof_state = self.get_proofread()
        if print_volume:
            link_or_volume = self.volume.name
            sort_value = ""
        else:
            link_or_volume = self.get_link()
            sort_value = f"data-sort-value=\"{self.sort_key}\""
        if len(self._chapters) > 1:
            row_string.append(f"rowspan={len(self._chapters)} {sort_value}|{link_or_volume}")
            row_string.append(f"rowspan={len(self._chapters)} style=\"background:{proof_color}\"|{proof_state}")
            row_string.append(f"rowspan={len(self._chapters)} {interwiki_sort_key}|{interwiki_links}")
        else:
            row_string.append(f"{sort_value}|{link_or_volume}")
            row_string.append(f"style=\"background:{proof_color}\"|{proof_state}")
            row_string.append(f"{interwiki_sort_key}|{interwiki_links}")
        for chapter in self._chapters:
            row_string.append(self._get_pages(chapter))
            row_string.append(self._get_author_str(chapter))
            year = self._get_death_year(chapter)
            row_string.append(f"{self._get_year_format(year)}|{year}")
            row_string.append("-")
        # remove the last entry again because the row separator only needed between rows
        if row_string[-1] == "-":
            row_string.pop(-1)
        return "\n|".join(row_string)

    def get_proofread(self) -> Tuple[str, str]:
        color = "#AA0000"
        status = "UNK"
        proof_state = self["proof_read"]
        if proof_state == 3:
            color = "#669966"
            status = "FER"
        elif proof_state == 2:
            color = "#556B2F"
            status = "KOR"
        return color, status

    @staticmethod
    def _escape_link_for_templates(link: str) -> str:
        return link.replace("=", "{{=}}")

    def get_link(self) -> str:
        redirect = self.lemma_dict["redirect"] if "redirect" in self.lemma_dict else False
        if redirect:
            link = f"[[RE:{self['lemma']}|''{{{{Anker2|{self._escape_link_for_templates(str(self['lemma']))}}}}}'']]"
            if isinstance(redirect, str):
                link += f" → '''[[RE:{redirect}|{redirect}]]'''"
        else:
            link = f"[[RE:{self['lemma']}|'''{{{{Anker2|{self._escape_link_for_templates(str(self['lemma']))}}}}}''']]"
        return link

    def get_wiki_links(self) -> Tuple[str, str]:
        link = ""
        sort_key = ""
        links = []
        sort_keys = []
        if "wp_link" in self:
            link, sort_key = self._process_wiki_link("wp")
            links.append(link)
            sort_keys.append(sort_key)
        if "ws_link" in self:
            link, sort_key = self._process_wiki_link("ws")
            links.append(link)
            sort_keys.append(sort_key)
        if "wd_link" in self:
            links.append(f"[[{self['wd_link']}|WD-Item]]")
            sort_keys.append(f"{self['wd_link']}")
        if links:
            link = "<br/>".join(links)
            sort_key = f"data-sort-value=\"{sort_keys[0]}\""
        return link, sort_key

    def _process_wiki_link(self, wiki_type: Literal["wp", "ws"]) -> Tuple[str, str]:
        link_type: Literal["ws_link", "wp_link"] = "ws_link"
        if wiki_type == "wp":
            link_type = "wp_link"
        parts = self._lemma_dict[link_type].split(":")
        return f"[[{self[link_type]}|{self._escape_link_for_templates(parts[-1])}" \
               f"<sup>({wiki_type.upper()} {parts[1]})</sup>]]", \
               f"{parts[0]}:{parts[1]}:{self.make_sort_key(':'.join(parts[2:]))}"

    def _get_pages(self, lemma_chapter: LemmaChapter) -> str:
        start_page_scan = lemma_chapter.start
        if start_page_scan % 2 == 0:
            start_page_scan -= 1
        pages_str = f"[[Special:Filepath/Pauly-Wissowa_{self._volume.name}," \
                    f"_{start_page_scan:04d}.jpg|{lemma_chapter.start}]]"
        if lemma_chapter.end and lemma_chapter.start != lemma_chapter.end:
            pages_str += f"-{lemma_chapter.end}"
        return pages_str

    def _get_author_str(self, lemma_chapter: LemmaChapter) -> str:
        author_str = ""
        if lemma_chapter.author:
            mapped_author = self._authors.get_author_by_mapping(lemma_chapter.author,
                                                                self._volume.name)
            if mapped_author:
                author_str = ", ".join([author.name for author in mapped_author])
            else:
                author_str = lemma_chapter.author
        return author_str

    def _get_death_year(self, lemma_chapter: LemmaChapter) -> str:
        year = ""
        if self._get_author_str(lemma_chapter):
            mapped_author = None
            if lemma_chapter.author:
                mapped_author = self._authors.get_author_by_mapping(lemma_chapter.author,
                                                                    self._volume.name)
            if mapped_author:
                years = [author.death for author in mapped_author if author.death]
                year = str(max(years)) if years else ""
            else:
                year = "????"
        return year

    @staticmethod
    def _get_year_format(year: str) -> str:
        green = "style=\"background:#B9FFC5\""
        red = "style=\"background:#FFCBCB\""
        gray = "style=\"background:#CBCBCB\""
        if year == "":
            year_format = gray
        else:
            try:
                content_free_year = datetime.now().year - 71
                if int(year) <= content_free_year:
                    year_format = green
                else:
                    year_format = red
            except (TypeError, ValueError):
                year_format = red
        return year_format

    def update_lemma_dict(self, update_dict: LemmaDict, remove_items: List[str] = None):
        for item_key in update_dict:
            # TypedDict only works with string literals
            self._lemma_dict[item_key] = update_dict[item_key]  # type: ignore
        if remove_items:
            for item in remove_items:
                if item in self._lemma_dict:
                    del self._lemma_dict[item]  # type: ignore
        self._recalc_lemma()
