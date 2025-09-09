from __future__ import annotations

from abc import ABC
from typing import Tuple, List, Callable, Mapping

from service.ws_re.register.lemma import Lemma


class Register(ABC):
    def __init__(self):
        self._lemmas: List[Lemma] = []
        self._registers: Mapping = {}

    def _init_lemmas(self, check_function: Callable):
        lemmas = []
        for register in self._registers.values():
            for lemma in register.lemmas:
                if check_function(lemma):
                    lemmas.append(lemma)
        self._lemmas = sorted(lemmas, key=lambda k: (k.get_sort_key(), k.volume.sort_key))

    @property
    def lemmas(self) -> List[Lemma]:
        return self._lemmas

    @staticmethod
    def squash_lemmas(lemmas: List[Lemma]) -> List[List[Lemma]]:
        return_lemmas = []
        last_lemmas: List[Lemma] = []
        for lemma in lemmas:
            if last_lemmas:
                if lemma.lemma == last_lemmas[-1].lemma:
                    last_lemmas.append(lemma)
                    continue
                return_lemmas.append(last_lemmas)
                last_lemmas = []
            last_lemmas.append(lemma)
        if last_lemmas:
            return_lemmas.append(last_lemmas)
        return return_lemmas

    def _get_table(self, print_volume: bool = True, print_description: bool = True,
                   print_author: bool = True, background: bool = False) -> str:
        header = f"""{{{{Tabellenstile}}}}
{{|class="wikitable sortable tabelle-kopf-fixiert"{' style=\"background:#FFFAF0;\"' if background else ''}
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
                chapter_sum += max(len(lemma.chapter_objects), 1)
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
                f"{multi_chapter} data-sort-value=\"{lemma.get_sort_key()}\"|{lemma.get_link()}".strip())
            if print_description:
                multi_chapter_items.append(f"\n|{multi_chapter}|"
                                           f"{self._get_short_description_line(lemmas)}")
            interwiki_line = self._get_interwiki_line(lemmas)
            multi_chapter_items.append(
                f"\n|{multi_chapter}"
                f"{' ' if (multi_chapter and interwiki_line != '|') else ''}"
                f"{interwiki_line}")
            table.append("".join(multi_chapter_items))
            table += table_rows
        table.append("|}")
        return "\n".join(table)

    @staticmethod
    def _get_interwiki_line(lemmas):
        interwiki_links = ""
        interwiki_sort_key = ""
        for lemma in lemmas:
            interwiki_links, interwiki_sort_key = lemma.get_wiki_links()
            if interwiki_links or interwiki_sort_key:
                break
        return f"{interwiki_sort_key if interwiki_sort_key else ''}|{interwiki_links}"

    @staticmethod
    def _get_short_description_line(lemmas):
        short_description = ""
        for lemma in lemmas:
            short_description = lemma.short_description
            if short_description:
                break
        return short_description if short_description else ""

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
