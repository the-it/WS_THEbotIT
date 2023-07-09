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

    def _get_table(self, print_volume: bool = True, print_description: bool = True, print_author: bool = True) -> str:
        header = f"""{{{{Tabellenstile}}}}
{{|class="wikitable sortable tabelle-kopf-fixiert"
!Artikel
{'!Kurztext' if print_description else ''}
!Wikilinks
{'!Band' if print_volume else ''}
!Seite
{'!Autor' if print_author else ''}
!Stat"""
        table = [header]
        for lemmas in self.squash_lemmas(self._lemmas):
            chapter_sum = 0
            table_rows = []
            for lemma in lemmas:
                # if there are no chapters ... one line must be added no madder what
                chapter_sum += max(len(lemma.chapters), 1)
                table_rows.append(lemma.get_table_row(print_volume=print_volume, print_author=print_author))
            # strip |-/n form the first line it is later replaced by the lemma line
            table_rows[0] = table_rows[0][3:]
            # take generell information from first template (no supplement)
            lemma = lemmas[0]
            multi_chapter = ""
            if chapter_sum > 1:
                multi_chapter = f"rowspan={chapter_sum}"
            multi_chapter_items = ["|-\n|"]
            multi_chapter_items.append(
                f"{multi_chapter} data-sort-value=\"{lemma.sort_key}\"|{lemma.get_link()}".strip())
            if print_description:
                multi_chapter_items.append(f"\n|{multi_chapter}|{lemma.short_description}")
            interwiki_links, interwiki_sort_key = lemma.get_wiki_links()
            multi_chapter_items.append(
                f"\n|{multi_chapter + '' if multi_chapter else ''}{interwiki_sort_key}|{interwiki_links}")
            table.append("".join(multi_chapter_items))
            table += table_rows
        table.append("|}")
        return "\n".join(table)

    @property
    def proof_read(self) -> Tuple[int, int, int, int, int]:
        fer = kor = nge = unk = vor = 0
        for lemma in self.lemmas:
            status, _ = lemma.status
            if status == "FER":
                fer += 1
            elif status == "KOR":
                kor += 1
            elif status.isdecimal():
                if lemma.exists:
                    vor += 1
                    continue
                nge += 1
            else:
                unk += 1
        return fer, kor, nge, vor, unk
