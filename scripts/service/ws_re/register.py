import json
import re
import unicodedata
from abc import ABC
from collections import OrderedDict
from collections.abc import Mapping
from datetime import datetime
from typing import Dict, Union, Sequence, Tuple, List, Any

from scripts.service.ws_re.data_types import _REGISTER_PATH, Volume, Volumes, VolumeType


class RegisterException(Exception):
    pass


class Author:
    def __init__(self, name: str, author_dict: Dict[str, int]):
        self._dict = author_dict
        if "_" in name:
            name = name.split("_")[0]
        self._name = name

    def __repr__(self):  # pragma: no cover
        return f"<AUTHOR - name:{self.name}, birth:{self.birth}, death:{self.death}>"

    @property
    def death(self) -> Union[int, None]:
        if "death" in self._dict.keys():
            return self._dict["death"]
        return None

    @property
    def birth(self) -> Union[int, None]:
        if "birth" in self._dict.keys():
            return self._dict["birth"]
        return None

    @property
    def name(self) -> str:
        return self._name

    def update_internal_dict(self, author_dict: Dict):
        self._dict.update(author_dict)

    def to_dict(self):
        return self._dict


class Authors:
    _REGISTER_PATH = _REGISTER_PATH

    def __init__(self):
        with open(self._REGISTER_PATH.joinpath("authors_mapping.json"), "r",
                  encoding="utf-8") as json_file:
            self._mapping = json.load(json_file)
        self._authors = {}
        with open(self._REGISTER_PATH.joinpath("authors.json"), "r",
                  encoding="utf-8") as json_file:
            json_dict = json.load(json_file)
            for author in json_dict:
                self._authors[author] = Author(author, json_dict[author])

    def get_author_by_mapping(self, name: str, issue: str) -> Union[Author, None]:
        author = None
        try:
            mapping = self._mapping[name]
            if isinstance(mapping, dict):
                try:
                    mapping = mapping[issue]
                except KeyError:
                    mapping = mapping["*"]
            author = self.get_author(mapping)
        except KeyError:
            pass
        return author

    def get_author(self, author_key: str):
        return self._authors[author_key]

    def set_mappings(self, mapping: Mapping):
        self._mapping.update(mapping)

    def set_author(self, mapping: Mapping):
        for author_key in mapping:
            if author_key in self._authors:
                self._authors[author_key].update_internal_dict(mapping[author_key])
            else:
                self._authors[author_key] = Author(author_key, mapping[author_key])

    def _to_dict(self):
        author_dict = dict()
        for dict_key in sorted(self._authors.keys()):
            author_dict[dict_key] = self._authors[dict_key].to_dict()
        return author_dict

    def persist(self):
        with open(self._REGISTER_PATH.joinpath("authors_mapping.json"), "w",
                  encoding="utf-8") as json_file:
            json.dump(self._mapping, json_file, sort_keys=True, indent=2, ensure_ascii=False)
        with open(self._REGISTER_PATH.joinpath("authors.json"), "w",
                  encoding="utf-8") as json_file:
            json.dump(self._to_dict(), json_file, sort_keys=True, indent=2, ensure_ascii=False)


class AuthorCrawler:
    _simple_mapping_regex = re.compile(r"\[\"([^\]]*)\"\]\s*=\s*\"([^\"]*)\"")
    _complex_mapping_regex = re.compile(r"\[\"([^\]]*)\"\]\s*=\s*\{([^\}]*)\}")

    @classmethod
    def get_mapping(cls, mapping: str) -> Dict[str, Union[str, Dict[str, str]]]:
        mapping_dict = {}
        for single_mapping in cls._split_mappings(mapping):
            mapping_dict.update(cls._extract_mapping(single_mapping))
        return mapping_dict

    @staticmethod
    def _split_mappings(mapping: str) -> Sequence[str]:
        mapping = re.sub(r"^return \{\n", "", mapping)
        mapping = re.sub(r"\}\s?$", "", mapping)
        splitted_mapping = mapping.split("\n[")
        splitted_mapping = ["[" + mapping.strip().strip(",").lstrip("[")
                            for mapping in splitted_mapping]
        return splitted_mapping

    @classmethod
    def _extract_mapping(cls, single_mapping: str) -> Dict[str, Union[str, Dict[str, str]]]:
        if "{" in single_mapping:
            return cls._extract_complex_mapping(single_mapping)
        hit = cls._simple_mapping_regex.search(single_mapping)
        return {hit.group(1): hit.group(2)}

    @classmethod
    def _extract_complex_mapping(cls, single_mapping: str) -> Dict[str, Dict[str, str]]:
        hit = cls._complex_mapping_regex.search(single_mapping)
        sub_dict = {}
        for sub_mapping in hit.group(2).split(",\n"):
            sub_hit = cls._simple_mapping_regex.search(sub_mapping)
            if sub_hit:
                sub_dict[sub_hit.group(1)] = sub_hit.group(2)
            else:

                sub_dict["*"] = sub_mapping.strip().strip("\"")
        return {hit.group(1): sub_dict}

    @classmethod
    def get_authors(cls, text: str):
        return_dict = {}
        author_list = cls._split_author_table(text)
        for author_sub_table in author_list:
            return_dict.update(cls._get_author(author_sub_table))
        return return_dict

    @staticmethod
    def _split_author_table(raw_table: str) -> List[str]:
        table = re.search(r"\{\|class=\"wikitable sortable\"\s+\|-\s+(.*)\s+\|\}",
                          raw_table, re.DOTALL).group(1)
        splitted_table = table.split("\n|-\n")
        del splitted_table[0]
        return splitted_table

    @staticmethod
    def _split_author(author_sub_table: str) -> List[str]:
        return author_sub_table.split("\n|")

    @staticmethod
    def _extract_author_name(author: str) -> Tuple[str, str]:
        author = author.lstrip("|")
        # replace all templates
        author = re.sub(r"\{\{[^\}]*\}\}", "", author)
        # if it's a link use only the second part
        if re.search(r"\[\[", author):
            author = author.split("|")[1]
        translation_dict = str.maketrans({"[": "", "]": "", "'": ""})
        author = author.translate(translation_dict)
        names = author.split(",")
        # handle funky things with a "="-character
        try:
            if "=" in names[0]:
                names[0] = names[0].split("=")[0].strip()
            if "=" in names[1]:
                names[1] = names[1].split("=")[0].strip()
        except IndexError:
            return names[0].strip(), ""
        return names[1].strip(), names[0].strip()

    @staticmethod
    def _extract_years(years: str) -> Tuple[Union[int, None], Union[int, None]]:
        hit = re.search(r"(?<!\")(\d{4})–?(\d{4})?", years)
        if hit:
            return int(hit.group(1)), int(hit.group(2)) if hit.group(2) else None
        return None, None

    @classmethod
    def _get_author(cls, author_lines: str) -> Mapping:
        lines = cls._split_author(author_lines)
        author_tuple = cls._extract_author_name(lines[0])
        years = cls._extract_years(lines[1])
        author = f"{author_tuple[0]} {author_tuple[1]}"
        author_dict = {author: {}}
        if years[0]:
            author_dict[author]["birth"] = years[0]
        if years[1]:
            author_dict[author]["death"] = years[1]
        return author_dict

    # after that get complete mapping


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

_POST_REGEX_RAW_LIST = [
    # catching of "a ...", "ab ..." and "ad ..."
    (r"^a[db]? ", ""),
    # catching of "X. ..."
    (r"^[a-z]?\. ", ""),
    # unify numbers
    (r"(?<!\d)(\d)(?!\d)", r"00\g<1>"),
    (r"(?<!\d)(\d\d)(?!\d)", r"0\g<1>")]

_POST_REGEX_LIST = []
for regex_pair in _POST_REGEX_RAW_LIST:
    _POST_REGEX_LIST.append((re.compile(regex_pair[0]), regex_pair[1]))

# some regex actions must performed before the TRANSLATION_DICT replacement

_PRE_REGEX_RAW_LIST = [
    (r"ου", "u"),
    (r"^(?:Ε|ε|η)", "he"),
    (r"^(?:Ι|ι)", "hi"),
    (r"^(?:Ο|ο)", "ho"),
    (r"^(?:Υ|υ)", "hy"),
    (r" (?:ε|η)", " he"),
    (r" ι", " hi"),
    (r" ο", " ho"),
    (r" υ", " hy"),
]

_PRE_REGEX_LIST = []
for regex_pair in _PRE_REGEX_RAW_LIST:
    _PRE_REGEX_LIST.append((re.compile(regex_pair[0]), regex_pair[1]))


class Lemma(Mapping):
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
        # remove all accents
        lemma = cls._strip_accents(lemma)
        # simple replacement of single characters
        for regex in _PRE_REGEX_LIST:
            lemma = regex[0].sub(regex[1], lemma)
        lemma = lemma.casefold().translate(_TRANSLATION_DICT)
        for regex in _POST_REGEX_LIST:
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
        if print_volume:
            link_or_volume = self.volume.name
            sort_value = ""
        else:
            link_or_volume = self.get_link()
            sort_value = f"data-sort-value=\"{self.sort_key}\""
        if len(self._chapters) > 1:
            row_string.append(f"rowspan={len(self._chapters)} {sort_value}|{link_or_volume}")
        else:
            row_string.append(f"{sort_value}|{link_or_volume}")
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
                link += f" → [[RE:{redirect}|{redirect}]]"
        else:
            link = f"[[RE:{self['lemma']}|{{{{Anker2|{self['lemma']}}}}}]]"
        return link

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


class Register(ABC):  # pylint: disable=too-few-public-methods
    @staticmethod
    def squash_lemmas(lemmas):
        return_lemmas = []
        last_lemmas = []
        for lemma in lemmas:
            if last_lemmas:
                if lemma["lemma"] == last_lemmas[-1]["lemma"]:
                    last_lemmas.append(lemma)
                    continue
                else:
                    return_lemmas.append(last_lemmas)
                    last_lemmas = []
            last_lemmas.append(lemma)
        if last_lemmas:
            return_lemmas.append(last_lemmas)
        return return_lemmas


class VolumeRegister(Register):
    _REGISTER_PATH = _REGISTER_PATH

    def __init__(self, volume: Volume, authors: Authors):
        self._authors = authors
        self._volume = volume
        with open(self._REGISTER_PATH.joinpath(f"{volume.file_name}.json"),
                  "r", encoding="utf-8") as json_file:
            lemma_list = json.load(json_file)
        self._lemmas = []
        for lemma in lemma_list:
            self._lemmas.append(Lemma(lemma, self._volume, self._authors))

    def __repr__(self):  # pragma: no cover
        return f"<VOLUME REGISTER - volume:{self.volume.name}, lemmas:{len(self.lemmas)}>"

    def __len__(self):
        return len(self._lemmas)

    @property
    def volume(self):
        return self._volume

    @property
    def lemmas(self):
        return self._lemmas

    def _get_table(self):
        header = """{|class="wikitable sortable"
!Artikel
!Seite
!Autor
!Sterbejahr"""
        table = [header]
        for lemma in self._lemmas:
            table.append(lemma.get_table_row())
        table.append("|}")
        return "\n".join(table)

    def _get_footer(self):
        return f"[[Kategorie:RE:Register|!]]\nZahl der Artikel: {len(self._lemmas)}, " \
               f"davon [[:Kategorie:RE:Band {self._volume.name}" \
               f"|{{{{PAGESINCATEGORY:RE:Band {self._volume.name}|pages}}}} in Volltext]]."

    def get_register_str(self):
        return f"{self._get_table()}\n{self._get_footer()}"

    def persist(self):
        persist_list = []
        for lemma in self.lemmas:
            persist_list.append(lemma.lemma_dict)
        with open(self._REGISTER_PATH.joinpath("{}.json".format(self._volume.file_name)),
                  "w", encoding="utf-8") as json_file:
            json.dump(persist_list, json_file, indent=2, ensure_ascii=False)

    def __getitem__(self, idx: int) -> Lemma:
        return self.lemmas[idx]

    def get_lemma_by_name(self, lemma_name: str, self_supplement: bool = False) -> Union[Lemma, None]:
        found_before = False
        for lemma in self.lemmas:
            if lemma["lemma"] == lemma_name:
                if found_before or not self_supplement:
                    return lemma
                found_before = True
        return None

    def get_lemma_by_sort_key(self, sort_key: str, self_supplement: bool = False) -> Union[Lemma, None]:
        # normalize it
        sort_key = Lemma.make_sort_key(sort_key)
        found_before = False
        for lemma in self.lemmas:
            if lemma.sort_key == sort_key:
                if found_before or not self_supplement:
                    return lemma
                found_before = True
        return None

    def get_index_of_lemma(self, lemma: Union[str, Lemma],
                           self_supplement: bool = False) -> Union[int, None]:
        if isinstance(lemma, str):
            lemma = self.get_lemma_by_name(lemma, self_supplement)
        if lemma:
            return self.lemmas.index(lemma)
        return None

    def __contains__(self, lemma_name: str) -> bool:
        return bool(self.get_lemma_by_name(lemma_name))

    @staticmethod
    def normalize_sort_key(lemma_dict: Dict[str, str]) -> str:
        if "sort_key" in lemma_dict:
            return Lemma.make_sort_key(lemma_dict["sort_key"])
        return Lemma.make_sort_key(lemma_dict["lemma"])

    def update_lemma(self, lemma_dict: Dict[str, str], remove_items: List) -> str:
        sort_key = self.normalize_sort_key(lemma_dict)

        if "lemma" in lemma_dict and lemma_dict["lemma"] in self:
            self._update_lemma_by_name(lemma_dict, remove_items)
            return "update_lemma_by_name"
        if self.get_lemma_by_sort_key(sort_key):
            self._update_by_sortkey(lemma_dict, remove_items)
            return "update_by_sortkey"
        if "previous" in lemma_dict and "next" in lemma_dict \
                and self.get_lemma_by_sort_key(Lemma.make_sort_key(lemma_dict["previous"])) \
                and self.get_lemma_by_sort_key(Lemma.make_sort_key(lemma_dict["next"])):
            self._update_pre_and_post_exists(lemma_dict)
            return "update_pre_and_post_exists"
        if "previous" in lemma_dict \
                and self.get_lemma_by_sort_key(Lemma.make_sort_key(lemma_dict["previous"])):
            self._update_pre_exists(lemma_dict)
            return "update_pre_exists"
        if "next" in lemma_dict \
                and self.get_lemma_by_sort_key(Lemma.make_sort_key(lemma_dict["next"])):
            self._update_post_exists(lemma_dict)
            return "update_post_exists"
        raise RegisterException(f"The update of the register {self.volume.name} "
                                f"with the dict {lemma_dict} is not possible. "
                                f"No strategy available")

    def _update_lemma_by_name(self, lemma_dict, remove_items):
        lemma_to_update = self.get_lemma_by_name(lemma_dict["lemma"])
        if self.volume.type == VolumeType.SUPPLEMENTS:
            self._update_in_supplements_with_neighbour_creation(lemma_to_update, lemma_dict, remove_items)
        else:
            lemma_to_update.update_lemma_dict(lemma_dict, remove_items)
            self._try_update_next_and_previous(lemma_dict, lemma_to_update)

    def _update_by_sortkey(self, lemma_dict: Dict[str, Any], remove_items: List[str]):
        lemma_to_update = self.get_lemma_by_sort_key(self.normalize_sort_key(lemma_dict))
        if self.volume.type == VolumeType.SUPPLEMENTS:
            self._update_in_supplements_with_neighbour_creation(lemma_to_update, lemma_dict, remove_items)
        else:
            self.try_update_previous_next_of_surrounding_lemmas(lemma_dict, lemma_to_update)
            lemma_to_update.update_lemma_dict(lemma_dict, remove_items)
            self._try_update_next_and_previous(lemma_dict, lemma_to_update)

    def _update_in_supplements_with_neighbour_creation(self,
                                                       lemma_to_update: Lemma,
                                                       lemma_dict: Dict[str, Union[str, List]],
                                                       remove_items: List[str]):
        lemma_to_update.update_lemma_dict(lemma_dict, remove_items)
        idx = self.get_index_of_lemma(lemma_to_update)
        if self[idx - 1].sort_key == Lemma.make_sort_key(lemma_dict["previous"]):
            self._try_update_previous(lemma_to_update, lemma_dict)
        else:
            self[idx - 1].update_lemma_dict({}, ["next"])
            self.lemmas.insert(idx,
                               Lemma({"lemma": lemma_dict["previous"], "next": lemma_dict["lemma"]},
                                     self.volume,
                                     self._authors))
        idx = self.get_index_of_lemma(lemma_to_update)
        if self[idx + 1].sort_key == Lemma.make_sort_key(lemma_dict["next"]):
            self._try_update_next(lemma_to_update, lemma_dict)
        else:
            self[idx + 1].update_lemma_dict({}, ["previous"])
            self.lemmas.insert(idx + 1,
                               Lemma({"lemma": lemma_dict["next"], "previous": lemma_dict["lemma"]},
                                     self.volume,
                                     self._authors))

    def _update_pre_and_post_exists(self, lemma_dict):
        pre_lemma = self.get_lemma_by_sort_key(Lemma.make_sort_key(lemma_dict["previous"]))
        post_lemma = self.get_lemma_by_sort_key(Lemma.make_sort_key(lemma_dict["next"]))
        post_idx = self.get_index_of_lemma(post_lemma)
        pre_idx = self.get_index_of_lemma(pre_lemma)
        if post_idx - pre_idx == 1:
            self.lemmas.insert(post_idx, Lemma(lemma_dict, self.volume, self._authors))
        elif post_idx - pre_idx == 2:
            self.lemmas[pre_idx + 1] = Lemma(lemma_dict, self.volume, self._authors)
        else:
            raise RegisterException(f"The update of the register {self.volume.name} "
                                    f"with the dict {lemma_dict} is not possible. "
                                    f"Diff between previous and next aren't 1 or 2")
        self._try_update_next_and_previous(lemma_dict, self[pre_idx + 1])

    def _update_pre_exists(self, lemma_dict):
        pre_lemma = self.get_lemma_by_sort_key(Lemma.make_sort_key(lemma_dict["previous"]))
        pre_idx = self.get_index_of_lemma(pre_lemma)
        # remove previous and next for gap
        post_lemma = self[pre_idx + 1]
        post_lemma.update_lemma_dict({}, ["previous"])
        try:
            del lemma_dict["next"]
        except KeyError:
            pass
        # insert lemma
        self.lemmas.insert(pre_idx + 1, Lemma(lemma_dict, self.volume, self._authors))
        self._try_update_previous(lemma_dict, self[pre_idx + 1])

    def _update_post_exists(self, lemma_dict):
        post_lemma = self.get_lemma_by_sort_key(Lemma.make_sort_key(lemma_dict["next"]))
        post_idx = self.get_index_of_lemma(post_lemma)
        # remove previous and next for gap
        pre_lemma = self[post_idx - 1]
        pre_lemma.update_lemma_dict({}, ["next"])
        try:
            del lemma_dict["previous"]
        except KeyError:
            pass
        # insert lemma
        self.lemmas.insert(post_idx, Lemma(lemma_dict, self.volume, self._authors))
        self._try_update_next(lemma_dict, self[post_idx])

    def _try_update_next_and_previous(self, new_lemma_dict: Dict[str, Any], lemma_to_update: Lemma):
        self._try_update_previous(lemma_to_update, new_lemma_dict)
        self._try_update_next(lemma_to_update, new_lemma_dict)

    def _try_update_next(self, lemma_to_update, new_lemma_dict):
        if "next" in new_lemma_dict:
            idx = self.get_index_of_lemma(lemma_to_update)
            next_lemma = self[idx + 1]
            next_lemma_dict = {"lemma": new_lemma_dict["next"],
                               "previous": new_lemma_dict["lemma"],
                               "next": next_lemma["next"]}
            if Lemma.make_sort_key(next_lemma_dict["lemma"]) == next_lemma.sort_key:
                next_lemma.update_lemma_dict(next_lemma_dict)
                try:
                    self.try_update_previous_next_of_surrounding_lemmas(next_lemma_dict, next_lemma)
                except RegisterException:
                    pass

    def _try_update_previous(self, lemma_to_update, new_lemma_dict):
        if "previous" in new_lemma_dict:
            idx = self.get_index_of_lemma(lemma_to_update)
            pre_lemma = self[idx - 1]
            pre_lemma_dict = {"lemma": new_lemma_dict["previous"],
                              "previous": pre_lemma["previous"],
                              "next": new_lemma_dict["lemma"]}
            if Lemma.make_sort_key(pre_lemma_dict["lemma"]) == pre_lemma.sort_key:
                pre_lemma.update_lemma_dict(pre_lemma_dict)
                try:
                    self.try_update_previous_next_of_surrounding_lemmas(pre_lemma_dict, pre_lemma)
                except RegisterException:
                    pass

    def try_update_previous_next_of_surrounding_lemmas(self, lemma_dict, lemma_to_update):
        idx = self.get_index_of_lemma(lemma_to_update)
        previous_test = False
        if lemma_to_update["previous"]:
            pre_lemma = self[idx - 1]
            try:
                previous_test = \
                    Lemma.make_sort_key(lemma_to_update["previous"]) == \
                    Lemma.make_sort_key(pre_lemma["lemma"]) == \
                    Lemma.make_sort_key(lemma_dict["previous"])
            except KeyError:
                pass
            if not previous_test:
                raise RegisterException(f"Current Lemma previous: \"{lemma_to_update['previous']}\""
                                        f" != previous lemma name \"{pre_lemma['lemma']}\" "
                                        f"!= new lemma value previous \"{lemma_dict.get('previous', 'no key')}\"")
        next_test = False
        if lemma_to_update["next"]:
            next_lemma = self[idx + 1]
            try:
                next_test = \
                    Lemma.make_sort_key(lemma_to_update["next"]) == \
                    Lemma.make_sort_key(next_lemma["lemma"]) == \
                    Lemma.make_sort_key(lemma_dict["next"])
            except KeyError:
                pass
            if not next_test:
                raise RegisterException(f"Current Lemma next: \"{lemma_to_update['next']}\" "
                                        f"!= next lemma name \"{next_lemma['lemma']}\" "
                                        f"!= new lemma value next \"{lemma_dict.get('next', 'no key')}\"")
        if previous_test:
            pre_lemma.update_lemma_dict({"next": lemma_dict["lemma"]})
        if next_test:
            next_lemma.update_lemma_dict({"previous": lemma_dict["lemma"]})


class AlphabeticRegister(Register):
    def __init__(self, start: str, end: str, registers: OrderedDict):
        self._start = start
        self._end = end
        self._registers = registers
        self._lemmas = []
        self._init_lemmas()

    def __repr__(self):  # pragma: no cover
        return f"<ALPHABETIC REGISTER - start:{self._start}, end:{self._end}, lemmas:{len(self)}>"

    def __len__(self):
        return len(self.squash_lemmas(self._lemmas))

    def __getitem__(self, item: int) -> Lemma:
        return self._lemmas[item]

    @property
    def start(self):
        return self._start

    def _init_lemmas(self):
        lemmas = []
        for volume_str in self._registers:
            for lemma in self._registers[volume_str].lemmas:
                if self._is_lemma_in_range(lemma):
                    lemmas.append(lemma)
        self._lemmas = sorted(lemmas, key=lambda k: (k.sort_key, k.volume.sort_key))

    def _is_lemma_in_range(self, lemma):
        append = True
        # include start
        if lemma.sort_key < self._start:
            append = False
        # exclude end
        elif lemma.sort_key >= self._end:
            append = False
        return append

    def _get_table(self):
        header = """{|class="wikitable sortable"
!Artikel
!Band
!Seite
!Autor
!Sterbejahr"""
        table = [header]
        for lemmas in self.squash_lemmas(self._lemmas):
            chapter_sum = 0
            table_rows = []
            lemma = None
            for lemma in lemmas:
                chapter_sum += len(lemma.chapters)
                table_rows.append(lemma.get_table_row(print_volume=True))
            # strip |-/n form the first line it is later replaced by the lemma line
            table_rows[0] = table_rows[0][3:]
            if chapter_sum > 1:
                table.append(f"|-\n|rowspan={chapter_sum} data-sort-value=\"{lemma.sort_key}\"|{lemma.get_link()}")
            else:
                table.append(f"|-\n|data-sort-value=\"{lemma.sort_key}\"|{lemma.get_link()}")
            table += table_rows
        table.append("|}")
        return "\n".join(table)

    def _get_footer(self):
        return "[[Kategorie:RE:Register|!]]\n" \
               f"Zahl der Artikel: {len(self._lemmas)}, "

    def get_register_str(self):
        return f"{self._get_table()}\n{self._get_footer()}"


class Registers:
    _RE_ALPHABET = ["a", "ak", "an", "ar", "as", "b", "c", "ch", "d", "di", "e", "er", "f", "g", "h", "hi", "i", "k",
                    "kl", "l", "lf", "m", "mb", "mi", "n", "o", "p", "pe", "pi", "po", "pr", "q", "r", "s", "se", "so",
                    "t", "th", "ti", "u", "uf", "x", "y", "z"]

    def __init__(self):
        self._authors = Authors()
        self._registers = OrderedDict()
        self._alphabetic_registers = OrderedDict()
        for volume in Volumes().all_volumes:
            try:
                self._registers[volume.name] = VolumeRegister(volume, self._authors)
            except FileNotFoundError:
                pass
        self._init_alphabetic_registers()

    def _init_alphabetic_registers(self):
        for idx, start in enumerate(self._RE_ALPHABET):
            end = "zzzzzz"
            try:
                end = self._RE_ALPHABET[idx + 1]
            except IndexError:
                pass
            finally:
                self._alphabetic_registers[start] = AlphabeticRegister(start, end, self._registers)

    def __getitem__(self, item) -> VolumeRegister:
        return self._registers[item]

    @property
    def alphabetic(self):
        return self._alphabetic_registers

    @property
    def volumes(self):
        return self._registers

    @property
    def authors(self):
        return self._authors

    def persist(self):
        for register in self._registers.values():
            register.persist()
