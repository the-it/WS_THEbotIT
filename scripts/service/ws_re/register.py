import json
import re
from abc import ABC
from collections import OrderedDict
from datetime import datetime
from typing import Dict, Union, Sequence

from scripts.service.ws_re.data_types import _REGISTER_PATH, Volume, ReDatenException, Volumes
from tools import path_or_str


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

    def get_author(self, mapping: str):
        return self._authors[mapping]


class AuthorCrawler:
    @staticmethod
    def get_mapping():
        pass

    @staticmethod
    def _split_mappings(mapping: str) -> Sequence[str]:
        mapping = re.sub(r"^return \{\n", "", mapping)
        mapping = re.sub(r"\}\s?$", "", mapping)
        splitted_mapping =  mapping.split("\n[")
        splitted_mapping = ["[" + mapping.strip().strip(",").lstrip("[") for mapping in splitted_mapping]
        return splitted_mapping


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


_TRANSLATION_DICT = str.maketrans({"v": "u",
                                   "w": "u",
                                   "j": "i",
                                   "(": "",
                                   ")": "",
                                   "?": ""})


class Lemma:
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
            raise ReDatenException("Error init RegisterLemma. Key missing in {}"
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
        # simple replacement of single characters
        lemma = self["lemma"].lower().translate(_TRANSLATION_DICT)
        # catching of "a ...", "ab ..." and "ad ..."
        return re.sub(r"^a(?:d|b)? ", "", lemma)

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
    _RE_ALPHABET = ["a", "ak", "an", "ar", "as", "b", "ca", "ch", "da", "di", "ea", "er", "f", "g",
                    "ha", "hi", "i", "k", "kl", "la", "li", "ma", "me", "mi", "n", "o", "p", "pe",
                    "pi", "po", "pr", "q", "r", "sa", "se", "so", "ta", "th", "ti", "u", "uf", "x",
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
