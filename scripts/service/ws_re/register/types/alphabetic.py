from typing import Dict, List, Optional

from scripts.service.ws_re.register.base import Register
from scripts.service.ws_re.register.lemma import Lemma
from scripts.service.ws_re.register.types.volume import VolumeRegister


class AlphabeticRegister(Register):
    def __init__(self,
                 start: str,
                 end: str,
                 before_start: Optional[str],
                 after_next_start: Optional[str],
                 registers: Dict[str, VolumeRegister]):
        self._start: str = start
        self._end: str = end
        self._before_start = before_start
        self._after_next_start = after_next_start
        self._registers = registers
        self._lemmas: List[Lemma] = []
        self._init_lemmas()

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

    def _init_lemmas(self):
        lemmas = []
        for volume_str in self._registers:
            for lemma in self._registers[volume_str].lemmas:
                if self._is_lemma_in_range(lemma):
                    lemmas.append(lemma)
        self._lemmas = sorted(lemmas, key=lambda k: (k.sort_key, k.volume.sort_key))

    def _is_lemma_in_range(self, lemma: Lemma) -> bool:
        append = True
        # include start
        if lemma.sort_key < self._start:
            append = False
        # exclude end
        elif lemma.sort_key >= self._end:
            append = False
        return append

    def _get_table(self) -> str:
        header = """{|class="wikitable sortable"
!Artikel
!Band
!Wikilinks
!Seite
!Autor
!Sterbejahr"""
        table = [header]
        for lemmas in self.squash_lemmas(self._lemmas):
            chapter_sum = 0
            table_rows = []
            lemma = None
            for lemma in lemmas:
                # if there are no chapters ... one line must be added no madder what
                chapter_sum += max(len(lemma.chapters), 1)
                table_rows.append(lemma.get_table_row(print_volume=True))
            # strip |-/n form the first line it is later replaced by the lemma line
            table_rows[0] = table_rows[0][3:]
            if chapter_sum > 1:
                table.append(f"|-\n|rowspan={chapter_sum} data-sort-value=\"{lemma.sort_key}\"|{lemma.get_link()}")
            else:
                table.append(f"|-\n|data-sort-value=\"{lemma.sort_key}\"|{lemma.get_link()}")
            table += table_rows
        table.append("|}")
        return "\n".join(table)

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
        fer, kor, unk = self.proof_read(self._lemmas)
        header.append(f"UNK={unk}")
        header.append(f"KOR={kor}")
        header.append(f"FER={fer}")
        return "{{" + "\n|".join(header) + "\n}}\n"

    def _get_footer(self) -> str:
        return "[[Kategorie:RE:Register|!]]\n" \
               f"Zahl der Artikel: {len(self._lemmas)}, "

    def get_register_str(self) -> str:
        return f"{self._get_header()}\n{self._get_table()}\n{self._get_footer()}"
