import json
from typing import Union, Dict, List, Any

from scripts.service.ws_re.register import _REGISTER_PATH
from scripts.service.ws_re.register.author import Authors
from scripts.service.ws_re.register.base import RegisterException, Register
from scripts.service.ws_re.register.lemma import Lemma
from scripts.service.ws_re.volumes import Volume, VolumeType


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
        if self.volume.type in (VolumeType.SUPPLEMENTS, VolumeType.REGISTER):
            self._update_in_supplements_with_neighbour_creation(lemma_to_update, lemma_dict, remove_items)
        else:
            lemma_to_update.update_lemma_dict(lemma_dict, remove_items)
            self._try_update_next_and_previous(lemma_dict, lemma_to_update)

    def _update_by_sortkey(self, lemma_dict: Dict[str, Any], remove_items: List[str]):
        lemma_to_update = self.get_lemma_by_sort_key(self.normalize_sort_key(lemma_dict))
        if self.volume.type in (VolumeType.SUPPLEMENTS, VolumeType.REGISTER):
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
            self._try_update_previous(lemma_dict, lemma_to_update)
        else:
            self[idx - 1].update_lemma_dict({}, ["next"])
            self.lemmas.insert(idx,
                               Lemma({"lemma": lemma_dict["previous"], "next": lemma_dict["lemma"]},
                                     self.volume,
                                     self._authors))
        idx = self.get_index_of_lemma(lemma_to_update)
        if self[idx + 1].sort_key == Lemma.make_sort_key(lemma_dict["next"]):
            self._try_update_next(lemma_dict, lemma_to_update)
        else:
            self[idx + 1].update_lemma_dict({}, ["previous"])
            self.lemmas.insert(idx + 1,
                               Lemma({"lemma": lemma_dict["next"], "previous": lemma_dict["lemma"]},
                                     self.volume,
                                     self._authors))

    def _update_pre_and_post_exists(self, lemma_dict: Dict[str, Any]):
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

    def _update_pre_exists(self, lemma_dict: Dict[str, Any]):
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

    def _update_post_exists(self, lemma_dict: Dict[str, Any]):
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
        self._try_update_previous(new_lemma_dict, lemma_to_update)
        self._try_update_next(new_lemma_dict, lemma_to_update)

    def _try_update_next(self, new_lemma_dict: Dict[str, Any], lemma_to_update: Lemma):
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

    def _try_update_previous(self, new_lemma_dict, lemma_to_update):
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

    def try_update_previous_next_of_surrounding_lemmas(self, lemma_dict: Dict[str, Any], lemma_to_update: Lemma):
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
