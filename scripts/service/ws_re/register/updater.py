from typing import Union, Dict, List, Any

from scripts.service.ws_re.register import _REGISTER_PATH
from scripts.service.ws_re.register.base import RegisterException
from scripts.service.ws_re.register.lemma import Lemma
from scripts.service.ws_re.register.volume import VolumeRegister
from scripts.service.ws_re.volumes import VolumeType


class Updater():
    _REGISTER_PATH = _REGISTER_PATH

    def __init__(self, volume_register: VolumeRegister):
        self._register = volume_register

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __repr__(self):  # pragma: no cover
        return f"<{self.__class__.__name__} - register:{self._register.volume.name}>"

    def update_lemma(self, lemma_dict: Dict[str, str], remove_items: List[str], self_supplement: bool = False) -> str:
        sort_key = VolumeRegister.normalize_sort_key(lemma_dict)

        if "lemma" in lemma_dict and self._register.get_lemma_by_name(lemma_dict["lemma"], self_supplement):
            self._update_lemma_by_name(lemma_dict, remove_items, self_supplement)
            return "update_lemma_by_name"
        if self._register.get_lemma_by_sort_key(sort_key):
            self._update_by_sortkey(lemma_dict, remove_items)
            return "update_by_sortkey"
        if "previous" in lemma_dict and "next" in lemma_dict \
                and self._register.get_lemma_by_sort_key(Lemma.make_sort_key(lemma_dict["previous"])) \
                and self._register.get_lemma_by_sort_key(Lemma.make_sort_key(lemma_dict["next"])):
            self._update_pre_and_post_exists(lemma_dict)
            return "update_pre_and_post_exists"
        if "previous" in lemma_dict \
                and self._register.get_lemma_by_sort_key(Lemma.make_sort_key(lemma_dict["previous"])):
            self._update_pre_exists(lemma_dict)
            return "update_pre_exists"
        if "next" in lemma_dict \
                and self._register.get_lemma_by_sort_key(Lemma.make_sort_key(lemma_dict["next"])):
            self._update_post_exists(lemma_dict)
            return "update_post_exists"
        raise RegisterException(f"The update of the register {self._register.volume.name} "
                                f"with the dict {lemma_dict} is not possible. "
                                f"No strategy available")

    def _update_lemma_by_name(self, lemma_dict: Dict[str, str], remove_items: List[str], self_supplement: bool):
        lemma_to_update = self._register.get_lemma_by_name(lemma_dict["lemma"], self_supplement)
        if self._register.volume.type in (VolumeType.SUPPLEMENTS, VolumeType.REGISTER):
            self._update_in_supplements_with_neighbour_creation(lemma_to_update, lemma_dict, remove_items)
        else:
            lemma_to_update.update_lemma_dict(lemma_dict, remove_items)
            self._try_update_next_and_previous(lemma_dict, lemma_to_update)

    def _update_by_sortkey(self, lemma_dict: Dict[str, Any], remove_items: List[str]):
        lemma_to_update = self._register.get_lemma_by_sort_key(self._register.normalize_sort_key(lemma_dict))
        if self._register.volume.type in (VolumeType.SUPPLEMENTS, VolumeType.REGISTER):
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
        idx = self._register.get_index_of_lemma(lemma_to_update)
        if self._register[idx - 1].sort_key == Lemma.make_sort_key(lemma_dict["previous"]):
            self._try_update_previous(lemma_dict, lemma_to_update)
        else:
            self._register[idx - 1].update_lemma_dict({}, ["next"])
            if not self._register.get_lemma_by_sort_key(lemma_dict["previous"]):
                self._register.lemmas.insert(idx,
                                             Lemma({"lemma": lemma_dict["previous"], "next": lemma_dict["lemma"]},
                                                   self._register.volume,
                                                   self._register.authors))
        idx = self._register.get_index_of_lemma(lemma_to_update)
        if self._register[idx + 1].sort_key == Lemma.make_sort_key(lemma_dict["next"]):
            self._try_update_next(lemma_dict, lemma_to_update)
        else:
            self._register[idx + 1].update_lemma_dict({}, ["previous"])
            if not self._register.get_lemma_by_sort_key(lemma_dict["next"]):
                self._register.lemmas.insert(idx + 1,
                                             Lemma({"lemma": lemma_dict["next"], "previous": lemma_dict["lemma"]},
                                                   self._register.volume,
                                                   self._register.authors))

    def _update_pre_and_post_exists(self, lemma_dict: Dict[str, Any]):
        pre_lemma = self._register.get_lemma_by_sort_key(Lemma.make_sort_key(lemma_dict["previous"]))
        post_lemma = self._register.get_lemma_by_sort_key(Lemma.make_sort_key(lemma_dict["next"]))
        post_idx = self._register.get_index_of_lemma(post_lemma)
        pre_idx = self._register.get_index_of_lemma(pre_lemma)
        if post_idx - pre_idx == 1:
            self._register.lemmas.insert(post_idx, Lemma(lemma_dict, self._register.volume, self._register.authors))
        elif post_idx - pre_idx == 2:
            self._register.lemmas[pre_idx + 1] = Lemma(lemma_dict, self._register.volume, self._register.authors)
        else:
            raise RegisterException(f"The update of the register {self._register.volume.name} "
                                    f"with the dict {lemma_dict} is not possible. "
                                    f"Diff between previous and next aren't 1 or 2")
        self._try_update_next_and_previous(lemma_dict, self._register[pre_idx + 1])

    def _update_pre_exists(self, lemma_dict: Dict[str, Any]):
        pre_lemma = self._register.get_lemma_by_sort_key(Lemma.make_sort_key(lemma_dict["previous"]))
        pre_idx = self._register.get_index_of_lemma(pre_lemma)
        # remove previous and next for gap
        post_lemma = self._register[pre_idx + 1]
        post_lemma.update_lemma_dict({}, ["previous"])
        try:
            del lemma_dict["next"]
        except KeyError:
            pass
        # insert lemma
        self._register.lemmas.insert(pre_idx + 1, Lemma(lemma_dict, self._register.volume, self._register.authors))
        self._try_update_previous(lemma_dict, self._register[pre_idx + 1])

    def _update_post_exists(self, lemma_dict: Dict[str, Any]):
        post_lemma = self._register.get_lemma_by_sort_key(Lemma.make_sort_key(lemma_dict["next"]))
        post_idx = self._register.get_index_of_lemma(post_lemma)
        # remove previous and next for gap
        pre_lemma = self._register[post_idx - 1]
        pre_lemma.update_lemma_dict({}, ["next"])
        try:
            del lemma_dict["previous"]
        except KeyError:
            pass
        # insert lemma
        self._register.lemmas.insert(post_idx, Lemma(lemma_dict, self._register.volume, self._register.authors))
        self._try_update_next(lemma_dict, self._register[post_idx])

    def _try_update_next_and_previous(self, new_lemma_dict: Dict[str, Any], lemma_to_update: Lemma):
        self._try_update_previous(new_lemma_dict, lemma_to_update)
        self._try_update_next(new_lemma_dict, lemma_to_update)

    def _try_update_next(self, new_lemma_dict: Dict[str, Any], lemma_to_update: Lemma):
        if "next" in new_lemma_dict:
            idx = self._register.get_index_of_lemma(lemma_to_update)
            next_lemma = self._register[idx + 1]
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
            idx = self._register.get_index_of_lemma(lemma_to_update)
            pre_lemma = self._register[idx - 1]
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
        idx = self._register.get_index_of_lemma(lemma_to_update)
        previous_test = False
        if lemma_to_update["previous"]:
            pre_lemma = self._register[idx - 1]
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
            next_lemma = self._register[idx + 1]
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
