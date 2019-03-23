import json
import re
from abc import ABC
from collections import OrderedDict
from collections.abc import Mapping
from datetime import datetime
from typing import Dict, Union, Sequence, Tuple, List

from scripts.service.ws_re.data_types import _REGISTER_PATH, Volume, Volumes
from tools import path_or_str


class RegisterException(Exception):
    pass


class Author:
    def __init__(self, name: str, author_dict: Dict[str, int]):
        self._dict = author_dict
        if "_" in name:
            name = name.split("_")[0]
        self._name = name

    def __repr__(self):  # pragma: no cover
        return "<AUTHOR - name:{}, birth:{}, death:{}>".format(self.name, self.birth, self.death)

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
        with open(path_or_str(self._REGISTER_PATH.joinpath("authors_mapping.json")), "r",
                  encoding="utf-8") as json_file:
            self._mapping = json.load(json_file)
        self._authors = {}
        with open(path_or_str(self._REGISTER_PATH.joinpath("authors.json")), "r",
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
        with open(path_or_str(self._REGISTER_PATH.joinpath("authors_mapping.json")), "w",
                  encoding="utf-8") as json_file:
            json.dump(self._mapping, json_file, sort_keys=True, indent=2, ensure_ascii=False)
        with open(path_or_str(self._REGISTER_PATH.joinpath("authors.json")), "w",
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
        author = "{} {}".format(author_tuple[0], author_tuple[1])
        author_dict = {author: {}}
        if years[0]:
            author_dict[author]["birth"] = years[0]
        if years[1]:
            author_dict[author]["death"] = years[1]
        return author_dict

    # after that get complete mapping


class LemmaChapter:
    def __init__(self, chapter_dict: Dict[str, Union[str, int]]):
        self._dict = chapter_dict

    def __repr__(self):  # pragma: no cover
        return "<LEMMA CHAPTER - start:{}, end:{}, author:{}>".format(self.start,
                                                                      self.end,
                                                                      self.author)

    def is_valid(self) -> bool:
        try:
            if "start" in self._dict and "end" in self._dict:
                return True
        except TypeError:
            pass
        return False

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


_TRANSLATION_DICT = {"a": "äâ",
                     "c": "ç",
                     "e": "èéêë",
                     "i": "jïî",
                     "o": "öô",
                     "s": "ś",
                     "u": "vwüûū",
                     "": "()?\'ʾʿ"}

_TMP_DICT = {}
for key in _TRANSLATION_DICT:
    for character in _TRANSLATION_DICT[key]:
        _TMP_DICT[character] = key
_TRANSLATION_DICT = str.maketrans(_TMP_DICT)


_REGEX_RAW_LIST = [
    # catching of "a ...", "ab ..." and "ad ..."
    (r"^a[db]? ", ""),
    # catching of "X. ..."
    (r"^[a-z]?\. ", ""),
    # unify numbers
    (r"(?<!\d)(\d)(?!\d)", r"00\g<1>"),
    (r"(?<!\d)(\d\d)(?!\d)", r"0\g<1>")]

_REGEX_LIST = []
for regex_pair in _REGEX_RAW_LIST:
    _REGEX_LIST.append((re.compile(regex_pair[0]), regex_pair[1]))


class Lemma(Mapping):
    def __init__(self,
                 lemma_dict: Dict[str, Union[str, list]],
                 volume: Volume,
                 authors: Authors):
        self._lemma_dict = lemma_dict
        self._authors = authors
        self._volume = volume
        self._chapters = []
        try:
            for chapter in self._lemma_dict["chapters"]:
                self._chapters.append(LemmaChapter(chapter))
        except KeyError:
            pass
        if not self.is_valid():
            raise RegisterException("Error init RegisterLemma. Key missing in {}"
                                    .format(self._lemma_dict))
        self._sort_key = self._make_sort_key()

    def __repr__(self):  # pragma: no cover
        return "<LEMMA - lemma:{}, previous:{}, next:{}, chapters:{}, volume:{}>"\
            .format(self["lemma"],
                    self["previous"],
                    self["next"],
                    len(self._chapters),
                    self._volume.name)

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

    def _make_sort_key(self):
        lemma = self["lemma"]
        # simple replacement of single characters
        lemma = lemma.casefold().translate(_TRANSLATION_DICT)

        for regex in _REGEX_LIST:
            lemma = regex[0].sub(regex[1], lemma)

        # delete dots at last
        lemma = lemma.replace(".", " ")
        return lemma.strip()

    def keys(self):
        return self._lemma_dict.keys()

    def is_valid(self) -> bool:
        if "lemma" not in self.keys() \
                or "chapters" not in self.keys():
            return False
        if not self._chapters:
            return False
        for chapter in self._chapters:
            if not chapter.is_valid():
                return False
        return True

    def get_table_row(self, print_volume: bool = False) -> str:
        row_string = ["|-"]
        link_or_volume = self.volume.name if print_volume else self.get_link()
        if len(self._chapters) > 1:
            row_string.append("rowspan={}|{}".format(len(self._chapters), link_or_volume))
        else:
            row_string.append(link_or_volume)
        for chapter in self._chapters:
            row_string.append(self._get_pages(chapter))
            row_string.append(self._get_author_str(chapter))
            year = self._get_death_year(chapter)
            row_string.append("{}|{}".format(self._get_year_format(year), year))
            row_string.append("-")
        # remove the last entry again because the row separator only needed between rows
        row_string.pop(-1)
        return "\n|".join(row_string)

    def get_link(self) -> str:
        return "[[RE:{lemma}|{{{{Anker2|{lemma}}}}}]]".format(lemma=self["lemma"])

    def _get_pages(self, lemma_chapter: LemmaChapter) -> str:
        start_page_scan = lemma_chapter.start
        if start_page_scan % 2 == 0:
            start_page_scan -= 1
        pages_str = "[[Special:Filepath/Pauly-Wissowa_{issue},_{start_page_scan:04d}.jpg|" \
                    "{start_page}]]"\
            .format(issue=self._volume.name,
                    start_page=lemma_chapter.start,
                    start_page_scan=start_page_scan)
        if lemma_chapter.start != lemma_chapter.end:
            pages_str += "-{}".format(lemma_chapter.end)
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
        with open(path_or_str(self._REGISTER_PATH.joinpath("{}.json".format(volume.file_name))),
                  "r", encoding="utf-8") as json_file:
            self._dict = json.load(json_file)
        self._lemmas = []
        for lemma in self._dict:
            self._lemmas.append(Lemma(lemma, self._volume, self._authors))

    def __repr__(self):  # pragma: no cover
        return "<VOLUME REGISTER - volume:{}, lemmas:{}>".format(self.volume.name, len(self.lemmas))

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
        return "[[Kategorie:RE:Register|!]]\n" \
               "Zahl der Artikel: {count_lemma}, " \
               "davon [[:Kategorie:RE:Band {volume}" \
               "|{{{{PAGESINCATEGORY:RE:Band {volume}|pages}}}} in Volltext]]."\
            .format(count_lemma=len(self._lemmas), volume=self._volume.name)

    def get_register_str(self):
        return "{}\n{}".format(self._get_table(), self._get_footer())


class AlphabeticRegister(Register):
    def __init__(self, start: str, end: str, registers: OrderedDict):
        self._start = start
        self._end = end
        self._registers = registers
        self._lemmas = []
        self._init_lemmas()

    def __repr__(self):  # pragma: no cover
        return "<ALPHABETIC REGISTER - start:{}, end:{}, lemmas:{}>"\
            .format(self._start, self._end, len(self))

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
                table.append("|-\n|rowspan={}|{}".format(chapter_sum, lemma.get_link()))
            else:
                table.append("|-\n|{}".format(lemma.get_link()))
            table += table_rows
        table.append("|}")
        return "\n".join(table)

    def _get_footer(self):
        return "[[Kategorie:RE:Register|!]]\n" \
               "Zahl der Artikel: {count_lemma}, ".format(count_lemma=len(self._lemmas))

    def get_register_str(self):
        return "{}\n{}".format(self._get_table(), self._get_footer())


class Registers:
    _RE_ALPHABET = ["a", "ak", "an", "ar", "as", "b", "c", "ch", "d", "di", "e", "er", "f", "g",
                    "h", "hi", "i", "k", "kl", "l", "lf", "m", "mb", "mi", "n", "o", "p", "pe",
                    "pi", "po", "pr", "q", "r", "s", "se", "so", "t", "th", "ti", "u", "uf", "x",
                    "y", "z"]

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
                self._alphabetic_registers[start] = AlphabeticRegister(start,
                                                                       end,
                                                                       self._registers)

    def __getitem__(self, item) -> VolumeRegister:
        return self._registers[item]

    @property
    def alphabetic(self):
        return self._alphabetic_registers

    @property
    def volumes(self):
        return self._registers
