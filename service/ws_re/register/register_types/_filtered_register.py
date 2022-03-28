from typing import Dict

from service.ws_re.register.register_types._base import Register
from service.ws_re.register.register_types.volume import VolumeRegister


class FilteredRegister(Register):
    def __init__(self, registers: Dict[str, VolumeRegister]):
        super().__init__()
        self._registers = registers

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
            table.append("".join(("|-\n|",
                                  f"{multi_chapter} data-sort-value=\"{lemma.sort_key}\"|{lemma.get_link()}".strip(),
                                  f"\n|{multi_chapter}|{lemma.short_description}")))
            table += table_rows
        table.append("|}")
        return "\n".join(table)

    def _init_lemmas(self, check_function):
        lemmas = []
        for volume_str in self._registers:
            for lemma in self._registers[volume_str].lemmas:
                if check_function(lemma):
                    lemmas.append(lemma)
        self._lemmas = sorted(lemmas, key=lambda k: (k.sort_key, k.volume.sort_key))
