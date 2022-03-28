from __future__ import annotations

from abc import ABC
from pathlib import Path
from typing import Tuple, List, TYPE_CHECKING

if TYPE_CHECKING:
    from service.ws_re.register.lemma import Lemma

_REGISTER_PATH: Path = Path(__file__).parent.joinpath("data")


class RegisterException(Exception):
    pass


class Register(ABC):
    def __init__(self):
        self._lemmas: List[Lemma] = []

    @property
    def lemmas(self) -> List[Lemma]:
        return self._lemmas

    @staticmethod
    def squash_lemmas(lemmas: List[Lemma]) -> List[List[Lemma]]:
        return_lemmas = []
        last_lemmas: List[Lemma] = []
        for lemma in lemmas:
            if last_lemmas:
                if lemma["lemma"] == last_lemmas[-1]["lemma"]:
                    last_lemmas.append(lemma)
                    continue
                return_lemmas.append(last_lemmas)
                last_lemmas = []
            last_lemmas.append(lemma)
        if last_lemmas:
            return_lemmas.append(last_lemmas)
        return return_lemmas

    @property
    def proof_read(self) -> Tuple[int, int, int]:
        fer = kor = unk = 0
        for lemma in self.lemmas:
            proof_read = lemma["proof_read"]
            if proof_read:
                if proof_read == 3:
                    fer += 1
                elif proof_read == 2:
                    kor += 1
                elif proof_read == 1:
                    unk += 1
        return fer, kor, unk

class FilteredRegister(Register):
    def _get_table(self) -> str:
        header = """{|class="wikitable sortable"
!Artikel
!Kurztext
!Band
!Status
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
            # take generell information from first template (no supplement)
            lemma = lemmas[0]
            multi_chapter = ""
            if chapter_sum > 1:
                multi_chapter = f"rowspan={chapter_sum}"
            table.append(f"|-\n|" +
                         f"{multi_chapter} data-sort-value=\"{lemma.sort_key}\"|{lemma.get_link()}".strip() +
                         f"\n|{multi_chapter}|{lemma.short_description}")
            table += table_rows
        table.append("|}")
        return "\n".join(table)
