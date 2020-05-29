import json
from typing import Union, Optional, List

from service.ws_re.register.authors import Authors
from service.ws_re.register._base import Register, _REGISTER_PATH
from service.ws_re.register.lemma import Lemma
from service.ws_re.register._typing import LemmaDict
from service.ws_re.volumes import Volume, Volumes


class VolumeRegister(Register):
    _REGISTER_PATH = _REGISTER_PATH

    def __init__(self, volume: Volume, authors: Authors):
        self._authors = authors
        self._volume = volume
        with open(self._REGISTER_PATH.joinpath(f"{volume.file_name}.json"),
                  "r", encoding="utf-8") as json_file:
            lemma_list = json.load(json_file)
        self._lemmas: List[Lemma] = []
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
!Status
!Wikilinks
!Seite
!Autor
!Sterbejahr"""
        table = [header]
        for lemma in self._lemmas:
            table.append(lemma.get_table_row())
        table.append("|}")
        return "\n".join(table)

    def _get_header(self) -> str:
        header = ["RERegister"]
        header.append(f"BAND={self.volume.name}")
        # calculate pre and post issue
        volumes = Volumes()
        vg, nf = volumes.get_neighbours(self.volume.name)
        header.append(f"VG={vg}")
        header.append(f"NF={nf}")
        header.append(f"SUM={len(self.lemmas)}")
        # calculate proof_read status
        fer, kor, unk = self.proof_read(self.lemmas)
        header.append(f"UNK={unk}")
        header.append(f"KOR={kor}")
        header.append(f"FER={fer}")
        return "{{" + "\n|".join(header) + "\n}}\n"

    def _get_footer(self) -> str:
        return f"[[Kategorie:RE:Register|!]]\nZahl der Artikel: {len(self._lemmas)}, " \
               f"davon [[:Kategorie:RE:Band {self._volume.name}" \
               f"|{{{{PAGESINCATEGORY:RE:Band {self._volume.name}|pages}}}} in Volltext]]."

    def get_register_str(self) -> str:
        return f"{self._get_header()}\n{self._get_table()}\n{self._get_footer()}"

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

    def get_index_of_lemma(self, lemma_input: Union[str, Lemma], self_supplement: bool = False) -> Optional[int]:
        if isinstance(lemma_input, str):
            lemma = self.get_lemma_by_name(lemma_input, self_supplement)
        else:
            lemma = lemma_input
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
