from collections import OrderedDict
from typing import Dict

from scripts.service.ws_re.register.alphabetic import AlphabeticRegister
from scripts.service.ws_re.register.author import Authors
from scripts.service.ws_re.register.volume import VolumeRegister
from scripts.service.ws_re.volumes import Volumes


class Registers:
    _RE_ALPHABET = ["a", "ak", "an", "ar", "as", "b", "c", "ch", "d", "di", "e", "er", "f", "g", "h", "hi", "i", "k",
                    "kl", "l", "lf", "m", "mb", "mi", "n", "o", "p", "pe", "pi", "po", "pr", "q", "r", "s", "se", "so",
                    "t", "th", "ti", "u", "uf", "x", "y", "z"]

    def __init__(self):
        self._authors = Authors()
        self._registers = OrderedDict()   # type: Dict[str, VolumeRegister]
        self._alphabetic_registers = OrderedDict()  # type: Dict[str, AlphabeticRegister]
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
