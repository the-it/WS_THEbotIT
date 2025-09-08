import json
from json import JSONDecodeError
from typing import Union, Optional, List, Iterator

from service.ws_re.register.authors import Authors
from service.ws_re.register.lemma import Lemma, LemmaDict
from service.ws_re.register.register_types._base import Register
from service.ws_re.register.repo import DataRepo
from service.ws_re.volumes import Volume, Volumes


class VolumeRegister(Register):
    def __init__(self, volume: Volume, authors: Authors):
        super().__init__()
        self._authors = authors
        self._volume = volume
        self.repo = DataRepo()
        with open(self.repo.get_data_path().joinpath(f"{volume.file_name}.json"),
                  "r", encoding="utf-8") as json_file:
            try:
                lemma_list = json.load(json_file)
            except JSONDecodeError as exception:
                raise ValueError(f"Decoding error in file {volume.file_name}") from exception
        for lemma in lemma_list:
            self._lemmas.append(Lemma.from_dict(lemma, self._volume, self._authors))

    def __repr__(self):
        return f"<{self.__class__.__name__} - volume:{self.volume.name}, lemmas:{len(self.lemmas)}>"

    def __len__(self):
        return len(self._lemmas)

    def __getitem__(self, idx: int) -> Lemma:
        return self.lemmas[idx]

    def __iter__(self) -> Iterator[Lemma]:
        yield from self.lemmas

    @property
    def volume(self) -> Volume:
        return self._volume

    @property
    def authors(self) -> Authors:
        return self._authors

    @property
    def lemmas(self) -> List[Lemma]:
        return self._lemmas

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
        fer, kor, unk = self.proof_read
        header.append(f"FER={fer}")
        header.append(f"KOR={kor}")
        header.append(f"UNK={unk}")
        return "{{" + "\n|".join(header) + "\n}}\n"

    def get_register_str(self, print_details: bool = True) -> str:
        table = self._get_table(print_volume=False, print_description=print_details, print_author=print_details)
        return f"{self._get_header()}" \
               f"\n{table}" \
               f"\n[[Kategorie:RE:Register|!]]"

    def persist(self):
        persist_list = []
        for lemma in self.lemmas:
            persist_list.append(lemma.to_dict())
        with open(self.repo.get_data_path().joinpath(f"{self._volume.file_name}.json"),
                  "w", encoding="utf-8") as json_file:
            json.dump(persist_list, json_file, indent=2, ensure_ascii=False)

    def get_lemma_by_name(self, lemma_name: str, self_supplement: bool = False) -> Optional[Lemma]:
        found_before = False
        for lemma in self.lemmas:
            if lemma.lemma == lemma_name:
                if found_before or not self_supplement:
                    return lemma
                found_before = True
        return None

    def get_lemma_by_sort_key(self, sort_key: str, self_supplement: bool = False) -> Optional[Lemma]:
        # normalize it
        sort_key = Lemma.make_sort_key(sort_key)
        found_before = False
        for lemma in self.lemmas:
            if lemma.get_sort_key() == sort_key:
                if found_before or not self_supplement:
                    return lemma
                found_before = True
        return None

    def get_index_of_lemma(self, lemma_input: Union[str, Lemma], self_supplement: bool = False) -> Optional[int]:
        if isinstance(lemma_input, str):
            lemma = self.get_lemma_by_name(lemma_input, self_supplement)
        elif self_supplement:
            lemma = self.get_lemma_by_name(lemma_input.lemma, self_supplement)
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
