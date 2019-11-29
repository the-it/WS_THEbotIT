import contextlib
from collections import OrderedDict
from typing import Dict, Generator

from scripts.service.ws_re.register.alphabetic import AlphabeticRegister
from scripts.service.ws_re.register.author import Authors
from scripts.service.ws_re.register.author_register import AuthorRegister
from scripts.service.ws_re.register.volume import VolumeRegister
from scripts.service.ws_re.volumes import Volumes


class Registers:
    _RE_ALPHABET = ["a", "ak", "an", "ar", "as", "b", "c", "ch", "d", "di", "e", "er", "f", "g", "h", "hi", "i", "k",
                    "kl", "l", "lf", "m", "mb", "mi", "n", "o", "p", "pe", "pi", "po", "pr", "q", "r", "s", "se", "so",
                    "t", "th", "ti", "u", "uf", "x", "y", "z"]

    def __init__(self):
        self._authors: Authors = Authors()
        self._registers: Dict[str, VolumeRegister] = OrderedDict()
        self._alphabetic_registers: Dict[str, AlphabeticRegister] = OrderedDict()
        for volume in Volumes().all_volumes:
            with contextlib.suppress(FileNotFoundError):
                self._registers[volume.name] = VolumeRegister(volume, self._authors)
        self._init_alphabetic_registers()

    def _init_alphabetic_registers(self):
        for idx, start in enumerate(self._RE_ALPHABET):
            end = "zzzzzz"
            before_start = None
            after_next_start = None
            with contextlib.suppress(IndexError):
                end = self._RE_ALPHABET[idx + 1]
            with contextlib.suppress(IndexError):
                before_start = self._RE_ALPHABET[idx - 1]
            with contextlib.suppress(IndexError):
                after_next_start = self._RE_ALPHABET[idx + 2]
            self._alphabetic_registers[start] = AlphabeticRegister(start, end,
                                                                   before_start, after_next_start,
                                                                   self._registers)

    def __getitem__(self, item) -> VolumeRegister:
        return self._registers[item]

    @property
    def alphabetic(self) -> Dict[str, AlphabeticRegister]:
        return self._alphabetic_registers

    @property
    def author(self) -> Generator[AuthorRegister, None, None]:
        for author in self.authors:
            register = AuthorRegister(author, self.authors, self._registers)
            if len(register) > 0:
                yield register

    @property
    def volumes(self) -> Dict[str, VolumeRegister]:
        return self._registers

    @property
    def authors(self) -> Authors:
        return self._authors

    def persist(self):
        for register in self._registers.values():
            register.persist()
