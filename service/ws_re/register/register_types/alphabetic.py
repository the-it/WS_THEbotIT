from typing import Dict, Optional

from service.ws_re.register.lemma import Lemma
from service.ws_re.register.register_types._base import Register
from service.ws_re.register.register_types.volume import VolumeRegister


class AlphabeticRegister(Register):
    def __init__(self,
                 start: str,
                 end: str,
                 before_start: Optional[str],
                 after_next_start: Optional[str],
                 registers: Dict[str, VolumeRegister]):
        super().__init__()
        self._registers = registers
        self._start: str = start
        self._end: str = end
        self._before_start = before_start
        self._after_next_start = after_next_start
        self._init_lemmas(self._is_lemma_in_range)

    def __repr__(self):
        return f"<{self.__class__.__name__} - start:{self._start}, end:{self._end}, lemmas:{len(self)}>"

    def __len__(self):
        return len(self.squash_lemmas(self._lemmas))

    def __getitem__(self, item: int) -> Lemma:
        return self._lemmas[item]

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    def _is_lemma_in_range(self, lemma: Lemma) -> bool:
        append = True
        # include start
        if lemma.get_sort_key() < self._start:
            append = False
        # exclude end
        elif lemma.get_sort_key() >= self._end:
            append = False
        return append

    def _get_header(self) -> str:
        header = ["RERegister"]
        header.append(f"ALPHABET={self.start}")
        if self._before_start:
            header.append(f"VG={self._before_start}")
        header.append(f"NF={self.end}")
        if self._after_next_start:
            header.append(f"NFNF={self._after_next_start}")
        header.append(f"SUM={len(self._lemmas)}")
        # calculate proof_read status
        fer, kor, nge, vor, unk = self.proof_read
        header.append(f"FER={fer}")
        header.append(f"KOR={kor}")
        header.append(f"NGE={nge}")
        header.append(f"VOR={vor}")
        header.append(f"UNK={unk}")
        return "{{" + "\n|".join(header) + "\n}}\n"

    def get_register_str(self) -> str:
        return f"{self._get_header()}\n{self._get_table(background=True)}\n[[Kategorie:RE:Register|!]]"
