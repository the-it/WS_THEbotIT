import contextlib
from typing import Optional

from service.ws_re.register._base import RegisterException, _REGISTER_PATH
from service.ws_re.register._typing import LemmaDict, UpdaterRemoveList
from service.ws_re.register.lemma import Lemma
from service.ws_re.register.register_types.volume import VolumeRegister
from service.ws_re.volumes import VolumeType


class Updater():
    _REGISTER_PATH = _REGISTER_PATH

    def __init__(self, volume_register: VolumeRegister):
        self._register = volume_register

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__} - register:{self._register.volume.name}>"

    def update_lemma(self, lemma_dict: LemmaDict, remove_items: UpdaterRemoveList,
                     self_supplement: bool = False) -> str:
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

    def _update_lemma_by_name(self, lemma_dict: LemmaDict, remove_items: UpdaterRemoveList, self_supplement: bool):
        lemma_to_update = self._register.get_lemma_by_name(lemma_dict["lemma"], self_supplement)
        if lemma_to_update:
            if self._register.volume.type in (VolumeType.SUPPLEMENTS, VolumeType.REGISTER):
                self._update_in_supplements_with_neighbour_creation(lemma_to_update, lemma_dict, remove_items)
            else:
                lemma_to_update.update_lemma_dict(lemma_dict, remove_items)
                self._try_update_next_and_previous(lemma_dict, lemma_to_update)

    def _update_by_sortkey(self, lemma_dict: LemmaDict, remove_items: UpdaterRemoveList):
        lemma_to_update = self._register.get_lemma_by_sort_key(self._register.normalize_sort_key(lemma_dict))
        if lemma_to_update:
            if self._register.volume.type in (VolumeType.SUPPLEMENTS, VolumeType.REGISTER):
                self._update_in_supplements_with_neighbour_creation(lemma_to_update, lemma_dict, remove_items)
            else:
                self.try_update_previous_next_of_surrounding_lemmas(lemma_dict, lemma_to_update)
                lemma_to_update.update_lemma_dict(lemma_dict, remove_items)
                self._try_update_next_and_previous(lemma_dict, lemma_to_update)

    def _update_in_supplements_with_neighbour_creation(self,
                                                       lemma_to_update: Lemma,
                                                       lemma_dict: LemmaDict,
                                                       remove_items: UpdaterRemoveList):
        lemma_to_update.update_lemma_dict(lemma_dict, remove_items)
        if lemma_to_update:
            idx = self._register.get_index_of_lemma(lemma_to_update)
            if idx:
                if idx > 0:
                    self._u_i_s_w_n_c_1(idx, lemma_dict, lemma_to_update)
                with contextlib.suppress(IndexError):
                    idx = self._register.get_index_of_lemma(lemma_to_update)
                    if idx:
                        self._u_i_s_w_n_c_2(idx, lemma_dict, lemma_to_update)

    def _u_i_s_w_n_c_2(self, idx: int, lemma_dict: LemmaDict, lemma_to_update: Lemma):
        if self._register[idx + 1].sort_key == Lemma.make_sort_key(lemma_dict["next"]) \
                or Lemma.make_sort_key(str(self._register[idx + 1]["lemma"])) \
                == Lemma.make_sort_key(lemma_dict["next"]):
            self._try_update_next(lemma_dict, lemma_to_update)
        else:
            self._register[idx + 1].update_lemma_dict({}, ["previous"])
            if not self._register.get_lemma_by_sort_key(lemma_dict["next"]):
                self._register.lemmas.insert(idx + 1,
                                             Lemma({"lemma": lemma_dict["next"],
                                                    "previous": lemma_dict["lemma"]},
                                                   self._register.volume,
                                                   self._register.authors))

    def _u_i_s_w_n_c_1(self, idx: int, lemma_dict: LemmaDict, lemma_to_update: Lemma):
        existing_pre_sortkey: str = self._register[idx - 1].sort_key
        processed_pre_sortkey = Lemma.make_sort_key(str(self._register[idx - 1]["lemma"]))
        if "previous" in lemma_dict:
            fetched_pre_sortkey = Lemma.make_sort_key(lemma_dict["previous"])
            if fetched_pre_sortkey in (existing_pre_sortkey, processed_pre_sortkey):
                self._try_update_previous(lemma_dict, lemma_to_update)
            else:
                self._register[idx - 1].update_lemma_dict({}, ["next"])
                if not self._register.get_lemma_by_sort_key(lemma_dict["previous"]):
                    self._register.lemmas.insert(idx,
                                                 Lemma({"lemma": lemma_dict["previous"],
                                                        "next": lemma_dict["lemma"]},
                                                       self._register.volume,
                                                       self._register.authors))

    def _update_pre_and_post_exists(self, lemma_dict: LemmaDict):
        pre_lemma = self._register.get_lemma_by_sort_key(Lemma.make_sort_key(lemma_dict["previous"]))
        post_lemma = self._register.get_lemma_by_sort_key(Lemma.make_sort_key(lemma_dict["next"]))
        if pre_lemma and post_lemma:
            pre_idx = self._register.get_index_of_lemma(pre_lemma)
            post_idx = self._register.get_index_of_lemma(post_lemma)
        else:
            return
        if pre_idx and post_idx:
            if post_idx - pre_idx == 1:
                self._register.lemmas.insert(post_idx,
                                             Lemma(lemma_dict, self._register.volume, self._register.authors))
            elif post_idx - pre_idx == 2:
                self._register.lemmas[pre_idx + 1] = Lemma(lemma_dict, self._register.volume, self._register.authors)
            else:
                raise RegisterException(f"The update of the register {self._register.volume.name} "
                                        f"with the dict {lemma_dict} is not possible. "
                                        f"Diff between previous and next aren't 1 or 2")
            self._try_update_next_and_previous(lemma_dict, self._register[pre_idx + 1])

    def _update_pre_exists(self, lemma_dict: LemmaDict):
        pre_lemma = self._register.get_lemma_by_sort_key(Lemma.make_sort_key(lemma_dict["previous"]))
        if pre_lemma:
            pre_idx = self._register.get_index_of_lemma(pre_lemma)
        else:
            return
        # remove previous and next for gap
        if pre_idx:
            with contextlib.suppress(IndexError):
                self._register[pre_idx + 1].update_lemma_dict({}, ["previous"])
            with contextlib.suppress(KeyError):
                del lemma_dict["next"]
            # insert lemma
            self._register.lemmas.insert(pre_idx + 1, Lemma(lemma_dict, self._register.volume, self._register.authors))
            self._try_update_previous(lemma_dict, self._register[pre_idx + 1])

    def _update_post_exists(self, lemma_dict: LemmaDict):
        post_lemma = self._register.get_lemma_by_sort_key(Lemma.make_sort_key(lemma_dict["next"]))
        if post_lemma:
            post_idx = self._register.get_index_of_lemma(post_lemma)
        else:
            return
        # remove previous and next for gap
        if post_idx:
            if post_idx - 1 > 0:
                pre_lemma = self._register[post_idx - 1]
                pre_lemma.update_lemma_dict({}, ["next"])
            with contextlib.suppress(KeyError):
                del lemma_dict["previous"]
            # insert lemma
            self._register.lemmas.insert(post_idx, Lemma(lemma_dict, self._register.volume, self._register.authors))
            self._try_update_next(lemma_dict, self._register[post_idx])

    def _try_update_next_and_previous(self, new_lemma_dict: LemmaDict, lemma_to_update: Lemma):
        self._try_update_previous(new_lemma_dict, lemma_to_update)
        self._try_update_next(new_lemma_dict, lemma_to_update)

    def _try_update_next(self, new_lemma_dict: LemmaDict, lemma_to_update: Lemma):
        if "next" in new_lemma_dict:
            idx = self._register.get_index_of_lemma(lemma_to_update)
            if idx:
                with contextlib.suppress(IndexError):
                    next_lemma = self._register[idx + 1]
                    next_lemma_dict: LemmaDict = {"lemma": new_lemma_dict["next"],
                                                  "previous": new_lemma_dict["lemma"]}
                    next_next_lemma: Optional[str] = str(next_lemma["next"]) if next_lemma["next"] else None
                    if next_next_lemma:
                        next_lemma_dict["next"] = next_next_lemma
                    if Lemma.make_sort_key(str(next_lemma_dict["lemma"])) == next_lemma.sort_key:
                        next_lemma.update_lemma_dict(next_lemma_dict)
                        with contextlib.suppress(RegisterException):
                            self.try_update_previous_next_of_surrounding_lemmas(next_lemma_dict, next_lemma)

    def _try_update_previous(self, new_lemma_dict: LemmaDict, lemma_to_update: Lemma):
        if "previous" in new_lemma_dict:
            idx = self._register.get_index_of_lemma(lemma_to_update)
            if idx:
                if idx - 1 < 0:
                    return
                pre_lemma = self._register[idx - 1]
                pre_lemma_dict: LemmaDict = {"lemma": new_lemma_dict["previous"],
                                             "next": new_lemma_dict["lemma"]}
                pre_pre_lemma: Optional[str] = str(pre_lemma["previous"]) if pre_lemma["previous"] else None
                if pre_pre_lemma:
                    pre_lemma_dict["previous"] = pre_pre_lemma
                if Lemma.make_sort_key(pre_lemma_dict["lemma"]) == pre_lemma.sort_key:
                    pre_lemma.update_lemma_dict(pre_lemma_dict)
                    with contextlib.suppress(RegisterException):
                        self.try_update_previous_next_of_surrounding_lemmas(pre_lemma_dict, pre_lemma)

    # todo: cut this pylint: disable=fixme
    # it will fail if there is no previous lemma and the next is able to update
    def try_update_previous_next_of_surrounding_lemmas(self, lemma_dict: LemmaDict, lemma_to_update: Lemma):
        idx = self._register.get_index_of_lemma(lemma_to_update)
        if idx is None:
            return
        previous_test = False
        pre_lemma = None
        if lemma_to_update["previous"]:
            if idx - 1 >= 0:
                # there is a lemma to update
                pre_lemma = self._register[idx - 1]
            else:
                # no lemma to update, we are done here
                return
            with contextlib.suppress(KeyError, TypeError):
                previous_test = \
                    Lemma.make_sort_key(str(lemma_to_update["previous"])) == \
                    Lemma.make_sort_key(str(pre_lemma["lemma"])) == \
                    Lemma.make_sort_key(lemma_dict["previous"])
            if not previous_test:
                raise RegisterException(f"Current Lemma previous: \"{lemma_to_update['previous']}\" "
                                        f"!= previous lemma name \"{pre_lemma['lemma'] if pre_lemma else pre_lemma}\" "
                                        f"!= new lemma value previous \"{lemma_dict.get('previous', 'no key')}\"")
        next_test = False
        next_lemma = None
        if lemma_to_update["next"]:
            try:
                # there is a next lemma to update
                next_lemma = self._register[idx + 1]
            except IndexError:
                # there is no next lemma we are done here
                return
            with contextlib.suppress(KeyError, TypeError):
                next_test = \
                    Lemma.make_sort_key(str(lemma_to_update["next"])) == \
                    Lemma.make_sort_key(str(next_lemma["lemma"])) == \
                    Lemma.make_sort_key(lemma_dict["next"])
            if not next_test:
                raise RegisterException(f"Current Lemma next: \"{lemma_to_update['next']}\" "
                                        f"!= next lemma name \"{next_lemma['lemma'] if next_lemma else next_lemma}\" "
                                        f"!= new lemma value next \"{lemma_dict.get('next', 'no key')}\"")
        if previous_test:
            if pre_lemma:
                pre_lemma.update_lemma_dict({"next": lemma_dict["lemma"]})
            else:
                raise RegisterException("Here went something wrong, pre_lemma is None.")
        if next_test:
            if next_lemma:
                next_lemma.update_lemma_dict({"previous": lemma_dict["lemma"]})
            else:
                raise RegisterException("Here went something wrong, next_lemma is None.")
