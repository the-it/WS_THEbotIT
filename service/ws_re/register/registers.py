import contextlib
from collections import OrderedDict
from datetime import datetime
from typing import Dict, Generator

from service.ws_re.register.authors import Authors
from service.ws_re.register.register_types.alphabetic import AlphabeticRegister
from service.ws_re.register.register_types.author import AuthorRegister
from service.ws_re.register.register_types.public_domain import PublicDomainRegister
from service.ws_re.register.register_types.short import ShortRegister
from service.ws_re.register.register_types.volume import VolumeRegister
from service.ws_re.volumes import Volumes

RE_ALPHABET = ["a", "ak", "an", "ar", "as", "b", "c", "ch", "d", "di", "e", "er", "f", "g", "h", "hi", "i", "k",
               "kl", "l", "lf", "m", "mb", "mi", "n", "o", "p", "pe", "pi", "po", "pr", "q", "r", "s", "se", "so",
               "t", "th", "ti", "u", "uf", "x", "y", "z"]


class Registers:
    def __init__(self):
        self._authors: Authors = Authors()
        self._registers: Dict[str, VolumeRegister] = OrderedDict()
        self._alphabetic_registers: Dict[str, AlphabeticRegister] = OrderedDict()
        for volume in Volumes().all_volumes:
            with contextlib.suppress(FileNotFoundError):
                self._registers[volume.name] = VolumeRegister(volume, self._authors)

    def __getitem__(self, item) -> VolumeRegister:
        return self._registers[item]

    @property
    def alphabetic(self) -> Generator[AlphabeticRegister, None, None]:
        for idx, start in enumerate(RE_ALPHABET):
            end = "zzzzzz"
            before_start = None
            after_next_start = None
            with contextlib.suppress(IndexError):
                end = RE_ALPHABET[idx + 1]
            with contextlib.suppress(IndexError):
                before_start = RE_ALPHABET[idx - 1]
            with contextlib.suppress(IndexError):
                after_next_start = RE_ALPHABET[idx + 2]
            yield AlphabeticRegister(start, end,
                                     before_start, after_next_start,
                                     self._registers)

    @property
    def author(self) -> Generator[AuthorRegister, None, None]:
        for author in self.authors:
            register = AuthorRegister(author, self.authors, self._registers)
            if len(register) > 0:
                yield register

    @property
    def short(self) -> Generator[ShortRegister, None, None]:
        for main_volume in Volumes().main_volumes:
            register = ShortRegister(main_volume, self._registers)
            yield register

    @property
    def pd(self) -> Generator[PublicDomainRegister, None, None]:
        current_year = datetime.now().year
        for year in range(current_year - 5, current_year + 5):
            register = PublicDomainRegister(year, self._authors, self._registers)
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
