import json
from typing import Union, Dict, Optional, List

from scripts.service.ws_re.register.author import Authors
from scripts.service.ws_re.register.base import Register, _REGISTER_PATH
from scripts.service.ws_re.register.lemma import Lemma, LemmaDict
from scripts.service.ws_re.volumes import Volume


class VolumeRegister(Register):
    _REGISTER_PATH = _REGISTER_PATH

    def __init__(self, volume: Volume, authors: Authors):
        self._authors = authors
        self._volume = volume
        with open(self._REGISTER_PATH.joinpath(f"{volume.file_name}.json"),
                  "r", encoding="utf-8") as json_file:
            lemma_list = json.load(json_file)
        self._lemmas = []  # type: List[Lemma]
        for lemma in lemma_list:
            self._lemmas.append(Lemma(lemma, self._volume, self._authors))

    def __repr__(self):
        return f"<{self.__class__.__name__} - volume:{self.volume.name}, lemmas:{len(self.lemmas)}>"

    def __len__(self):
        return len(self._lemmas)

    @property
    def volume(self) -> Volume:
        return self._volume

    @property
    def authors(self) -> Authors:
        return self._authors

    @property
    def lemmas(self) -> List[Lemma]:
        return self._lemmas

    def _get_table(self) -> str:
        header = """{|class="wikitable sortable"
!Artikel
!Wikilinks
!Seite
!Autor
!Sterbejahr"""
        table = [header]
        for lemma in self._lemmas:
            table.append(lemma.get_table_row())
        table.append("|}")
        return "\n".join(table)

    def _get_footer(self) -> str:
        return f"[[Kategorie:RE:Register|!]]\nZahl der Artikel: {len(self._lemmas)}, " \
               f"davon [[:Kategorie:RE:Band {self._volume.name}" \
               f"|{{{{PAGESINCATEGORY:RE:Band {self._volume.name}|pages}}}} in Volltext]]."

    def get_register_str(self) -> str:
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

    def get_lemma_by_name(self, lemma_name: str, self_supplement: bool = False) -> Optional[Lemma]:
        found_before = False
        for lemma in self.lemmas:
            if lemma["lemma"] == lemma_name:
                if found_before or not self_supplement:
                    return lemma
                found_before = True
        return None

    def get_lemma_by_sort_key(self, sort_key: str, self_supplement: bool = False) -> Optional[Lemma]:
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
                           self_supplement: bool = False) -> Optional[int]:
        if isinstance(lemma, str):
            lemma = self.get_lemma_by_name(lemma, self_supplement)
        if lemma:
            return self.lemmas.index(lemma)
        return None

    def __contains__(self, lemma_name: str) -> bool:
        return bool(self.get_lemma_by_name(lemma_name))

    @staticmethod
    def normalize_sort_key(lemma_dict: LemmaDict) -> str:
        if "sort_key" in lemma_dict:
            return Lemma.make_sort_key(lemma_dict["sort_key"])
        return Lemma.make_sort_key(lemma_dict["lemma"])
