from __future__ import annotations

from abc import ABC
from typing import Tuple, List, Callable, Mapping

from service.ws_re.register.lemma import Lemma


class Register(ABC):
    def __init__(self):
        self._lemmas: List[Lemma] = []
        self._registers: Mapping = None

    def _init_lemmas(self, check_function: Callable):
        lemmas = []
        for volume_str in self._registers:
            for lemma in self._registers[volume_str].lemmas:
                if check_function(lemma):
                    lemmas.append(lemma)
        self._lemmas = sorted(lemmas, key=lambda k: (k.sort_key, k.volume.sort_key))

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

    def _get_table(self, print_volume: bool = True) -> str:
        header = f"""{{|class="wikitable sortable"
!Artikel
!Kurztext
!Wikilinks
{'!Band' if print_volume else ''}
!Seite
!Autor
!Stat"""
        table = [header]
        for lemmas in self.squash_lemmas(self._lemmas):
            chapter_sum = 0
            table_rows = []
            for lemma in lemmas:
                # if there are no chapters ... one line must be added no madder what
                chapter_sum += max(len(lemma.chapters), 1)
                table_rows.append(lemma.get_table_row(print_volume=print_volume))
            # strip |-/n form the first line it is later replaced by the lemma line
            table_rows[0] = table_rows[0][3:]
            # take generell information from first template (no supplement)
            lemma = lemmas[0]
            multi_chapter = ""
            if chapter_sum > 1:
                multi_chapter = f"rowspan={chapter_sum}"
            interwiki_links, interwiki_sort_key = lemma.get_wiki_links()
            table.append("".join(("|-\n|",
                                  f"{multi_chapter} data-sort-value=\"{lemma.sort_key}\"|{lemma.get_link()}".strip(),
                                  f"\n|{multi_chapter}|{lemma.short_description}",
                                  f"\n|{multi_chapter + '' if multi_chapter else ''}"
                                  f"{interwiki_sort_key}|{interwiki_links}")))
            table += table_rows
        table.append("|}")
        return "\n".join(table)

    @property
    def proof_read(self) -> Tuple[int, int, int]:
        fer = kor = unk = 0
        for lemma in self.lemmas:
            status, _ = lemma.status
            if status == "FER":
                fer += 1
            elif status == "KOR":
                kor += 1
            else:
                unk += 1
        return fer, kor, unk
