import re
import unicodedata
from collections import OrderedDict
from datetime import datetime
from typing import Dict, Union, List, Tuple

from scripts.service.ws_re.register.author import Authors
from scripts.service.ws_re.register.base import RegisterException
from scripts.service.ws_re.volumes import Volume


class LemmaChapter:
    _keys = ["start", "end", "author"]

    def __init__(self, chapter_dict: Dict[str, Union[str, int]]):
        self._dict = chapter_dict

    def __repr__(self):  # pragma: no cover
        return f"<LEMMA CHAPTER - start:{self.start}, end:{self.end}, author:{self.author}>"

    def is_valid(self) -> bool:
        try:
            if "start" in self._dict and "end" in self._dict:
                return True
        except TypeError:
            pass
        return False

    def get_dict(self) -> Dict[str, str]:
        return_dict = OrderedDict()
        for property_key in self._keys:
            if property_key in self._dict:
                return_dict[property_key] = self._dict[property_key]
        return return_dict

    @property
    def start(self) -> int:
        return self._dict["start"]

    @property
    def end(self) -> int:
        return self._dict["end"]

    @property
    def author(self) -> Union[str, None]:
        if "author" in self._dict.keys():
            return self._dict["author"]
        return None


_TRANSLATION_DICT = {"a": "α",
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

for key in _TRANSLATION_DICT:
    for character in _TRANSLATION_DICT[key]:
        _TMP_DICT[character] = key
_TRANSLATION_DICT = str.maketrans(_TMP_DICT)

_3rd_REGEX_RAW_LIST = [
    # catching of "a ...", "ab ..." and "ad ..."
    (r"^a[db]? ", ""),
    # catching of "X. ..."
    (r"^[a-z]?\. ", ""),
    # unify numbers
    (r"(?<!\d)(\d)(?!\d)", r"00\g<1>"),
    (r"(?<!\d)(\d\d)(?!\d)", r"0\g<1>")]

_3rd_REGEX_LIST = []
for regex_pair in _3rd_REGEX_RAW_LIST:
    _3rd_REGEX_LIST.append((re.compile(regex_pair[0]), regex_pair[1]))

# some regex actions must performed before the TRANSLATION_DICT replacement

_2nd_REGEX_RAW_LIST = [
    (r"αυ", "au"),
    (r"ευ", "eu"),
    (r"ου", "u"),
]

_2nd_REGEX_LIST = []
for regex_pair in _2nd_REGEX_RAW_LIST:
    _2nd_REGEX_LIST.append((re.compile(regex_pair[0]), regex_pair[1]))

_1st_REGEX_RAW_LIST = [
    (r"^(?:ἑ|ἡ|ἥ)", "he"),
    (r"^ἱ", "hi"),
    (r"^ὁ", "ho"),
    (r"^ὑ", "hy"),
    (r" (?:ἑ|ἡ|ἥ)", " he"),
    (r" ἱ", " hi"),
    (r" ὁ", " ho"),
    (r" ὑ", " hy"),
]

_1st_REGEX_LIST = []
for regex_pair in _1st_REGEX_RAW_LIST:
    _1st_REGEX_LIST.append((re.compile(regex_pair[0]), regex_pair[1]))


class Lemma():
    _keys = ["lemma", "previous", "next", "sort_key", "redirect", "wp_link", "ws_link", "chapters"]

    def __init__(self,
                 lemma_dict: Dict[str, Union[str, list]],
                 volume: Volume,
                 authors: Authors):
        self._lemma_dict = lemma_dict
        self._authors = authors
        self._volume = volume
        self._chapters = []
        self._sort_key = ""
        if "chapters" in lemma_dict and lemma_dict["chapters"]:
            self._init_chapters()
        self._set_sort_key()

    def _init_chapters(self):
        self._chapters = []
        try:
            for chapter in self._lemma_dict["chapters"]:
                self._chapters.append(LemmaChapter(chapter))
        except KeyError:
            pass
        if not self.is_valid():
            raise RegisterException(f"Error init RegisterLemma. Key missing in {self._lemma_dict}")

    def __repr__(self):  # pragma: no cover
        return f"<LEMMA - lemma:{self['lemma']}, previous:{self['previous']}, next:{self['next']}, " \
            f"chapters:{len(self._chapters)}, volume:{self._volume.name}>"

    def __getitem__(self, item):
        try:
            return self._lemma_dict[item]
        except KeyError:
            return None

    def __len__(self):
        return len(self._lemma_dict)

    def __iter__(self):
        return iter(self._lemma_dict)

    @property
    def volume(self):
        return self._volume

    @property
    def chapters(self):
        return self._chapters

    @property
    def sort_key(self):
        return self._sort_key

    def _set_sort_key(self):
        if self["sort_key"]:
            lemma = self["sort_key"]
        else:
            lemma = self["lemma"]
        self._sort_key = self.make_sort_key(lemma)

    @staticmethod
    def _strip_accents(accent_string):
        return ''.join(unicode_char for unicode_char in unicodedata.normalize('NFD', accent_string)
                       if unicodedata.category(unicode_char) != 'Mn')

    @classmethod
    def make_sort_key(cls, lemma: str):
        lemma = lemma.casefold()
        # handle some things that need regex with accents
        for regex in _1st_REGEX_LIST:
            lemma = regex[0].sub(regex[1], lemma)
        # remove all accents
        lemma = cls._strip_accents(lemma)
        # simple replacement of single characters
        for regex in _2nd_REGEX_LIST:
            lemma = regex[0].sub(regex[1], lemma)
        lemma = lemma.translate(_TRANSLATION_DICT)
        for regex in _3rd_REGEX_LIST:
            lemma = regex[0].sub(regex[1], lemma)
        # delete dots at last
        lemma = lemma.replace(".", " ")
        return lemma.strip()

    def keys(self):
        return self._lemma_dict.keys()

    @property
    def lemma_dict(self) -> Dict[str, Union[str, List[Dict[str, str]]]]:
        return_dict = OrderedDict()
        for property_key in self._keys:
            if property_key in self.keys():
                if property_key == "chapters":
                    value = self._get_chapter_dicts()
                else:
                    value = self._lemma_dict[property_key]
                return_dict[property_key] = value
        return return_dict

    def _get_chapter_dicts(self) -> List[Dict[str, str]]:
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
        if print_volume:
            link_or_volume = self.volume.name
            sort_value = ""
        else:
            link_or_volume = self.get_link()
            sort_value = f"data-sort-value=\"{self.sort_key}\""
        if len(self._chapters) > 1:
            row_string.append(f"rowspan={len(self._chapters)} {sort_value}|{link_or_volume}")
            row_string.append(f"rowspan={len(self._chapters)} {interwiki_sort_key}|{interwiki_links}")
        else:
            row_string.append(f"{sort_value}|{link_or_volume}")
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

    def get_link(self) -> str:
        redirect = self.lemma_dict["redirect"] if "redirect" in self.lemma_dict else False
        if redirect:
            link = f"[[RE:{self['lemma']}|''{{{{Anker2|{self['lemma']}}}}}'']]"
            if isinstance(redirect, str):
                link += f" → {{{{RE siehe|{redirect}|'''{redirect}'''}}}}"
        else:
            link = f"[[RE:{self['lemma']}|'''{{{{Anker2|{self['lemma']}}}}}''']]"
        return link

    def get_wiki_links(self) -> Tuple[str, str]:
        link = ""
        sort_key = ""
        links = []
        sort_keys = []
        if "wp_link" in self:
            parts = self['wp_link'].split(":")
            links.append(f"[[{self['wp_link']}|{parts[2]}<sup>(WP {parts[1]})</sup>]]")
            sort_keys.append(f"{parts[0]}:{parts[1]}:{self.make_sort_key(parts[2])}")
        if "ws_link" in self:
            parts = self['ws_link'].split(":")
            links.append(f"[[{self['ws_link']}|{parts[2]}<sup>(WS {parts[1]})</sup>]]")
            sort_keys.append(f"{parts[0]}:{parts[1]}:{self.make_sort_key(parts[2])}")
        if links:
            link = "<br/>".join(links)
            sort_key = f"data-sort-value=\"{sort_keys[0]}\""
        return link, sort_key

    def _get_pages(self, lemma_chapter: LemmaChapter) -> str:
        start_page_scan = lemma_chapter.start
        if start_page_scan % 2 == 0:
            start_page_scan -= 1
        pages_str = f"[[Special:Filepath/Pauly-Wissowa_{self._volume.name}," \
            f"_{start_page_scan:04d}.jpg|{lemma_chapter.start}]]"
        if lemma_chapter.start != lemma_chapter.end:
            pages_str += f"-{lemma_chapter.end}"
        return pages_str

    def _get_author_str(self, lemma_chapter: LemmaChapter) -> str:
        author_str = ""
        if lemma_chapter.author:
            mapped_author = self._authors.get_author_by_mapping(lemma_chapter.author,
                                                                self._volume.name)
            if mapped_author:
                author_str = mapped_author.name
            else:
                author_str = lemma_chapter.author
        return author_str

    def _get_death_year(self, lemma_chapter: LemmaChapter) -> str:
        year = ""
        if self._get_author_str(lemma_chapter):
            mapped_author = self._authors.get_author_by_mapping(lemma_chapter.author,
                                                                self._volume.name)
            if mapped_author:
                year = str(mapped_author.death) if mapped_author.death else ""
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
                year = int(year)
                content_free_year = datetime.now().year - 71
                if year <= content_free_year:
                    year_format = green
                else:
                    year_format = red
            except (TypeError, ValueError):
                year_format = red
        return year_format

    def update_lemma_dict(self, update_dict: Dict, remove_items: List = None):
        for item_key in update_dict:
            self._lemma_dict[item_key] = update_dict[item_key]
        if remove_items:
            for item in remove_items:
                if item in self._lemma_dict:
                    del self._lemma_dict[item]
        self._init_chapters()
        self._set_sort_key()
