from typing import Dict, List

from service.ws_re.register._base import Register
from service.ws_re.register.lemma import Lemma
from service.ws_re.register.register_types.volume import VolumeRegister


class ShortRegister(Register):
    def __init__(self,
                 main_issue: str,
                 registers: Dict[str, VolumeRegister]):
        self._main_issue: str = main_issue
        self._registers = registers
        self._lemmas: List[Lemma] = []
        self._init_lemmas()

    def __repr__(self):
        return f"<{self.__class__.__name__} - main_issue:{self._main_issue}, lemmas:{len(self)}>"

    def __len__(self):
        return len(self._lemmas)

    def _init_lemmas(self):
        lemmas = []
        for volume_str in self._registers:
            if self._main_issue in volume_str:
                for lemma in self._registers[volume_str].lemmas:
                    if lemma not in lemmas:
                        lemmas.append(lemma)
        self._lemmas = lemmas

    def _get_table(self) -> str:
        table = []
        for lemma in self._lemmas:
            table.append(f"[[RE:{lemma}|{lemma}]]")
        return " |\n".join(table)

    def get_register_str(self) -> str:
        return self._get_table()
