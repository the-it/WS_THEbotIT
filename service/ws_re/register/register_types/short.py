from typing import Dict

from service.ws_re.register._base import Register
from service.ws_re.register.register_types.volume import VolumeRegister
from service.ws_re.volumes import Volumes


class ShortRegister(Register):
    def __init__(self,
                 main_issue: str,
                 registers: Dict[str, VolumeRegister]):
        super().__init__()
        self.main_issue: str = main_issue
        self._registers = registers
        self._init_lemmas()

    def __repr__(self):
        return f"<{self.__class__.__name__} - main_issue:{self.main_issue}, lemmas:{len(self)}>"

    def __len__(self):
        return len(self._lemmas)

    def _init_lemmas(self):
        lemmas = []
        for volume_str in self._registers:
            if Volumes.is_volume_part_of_main_volume(volume_str, self.main_issue):
                for lemma in self._registers[volume_str].lemmas:
                    if lemma not in lemmas:
                        lemmas.append(lemma)
        self._lemmas = lemmas

    def get_register_str(self) -> str:
        table = []
        for lemma in self.squash_lemmas(sorted(self._lemmas, key=lambda k: (k.sort_key, k.volume.sort_key))):
            lemma_str = lemma[0]["lemma"]
            table.append(f"[[RE:{lemma_str}|{lemma_str}]]")
        return " |\n".join(table)
