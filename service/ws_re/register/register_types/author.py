from typing import Dict, Tuple

from service.ws_re.register._base import Register
from service.ws_re.register.author import Author
from service.ws_re.register.authors import Authors
from service.ws_re.register.lemma import Lemma
from service.ws_re.register.register_types.volume import VolumeRegister


class AuthorRegister(Register):
    def __init__(self,
                 author: Author,
                 authors: Authors,
                 registers: Dict[str, VolumeRegister]):
        super().__init__()
        self._author: Author = author
        self._authors: Authors = authors
        self._registers = registers
        self._init_lemmas()

    def __repr__(self):
        return f"<{self.__class__.__name__} - author:{self._author}, lemmas:{len(self)}>"

    def __len__(self):
        return len(self._lemmas)

    def __getitem__(self, item: int) -> Lemma:
        return self._lemmas[item]

    @property
    def author(self):
        return self._author

    def _init_lemmas(self):
        lemmas = []
        for volume_str in self._registers:
            for lemma in self._registers[volume_str].lemmas:
                if self._is_lemma_of_author(lemma):
                    lemmas.append(lemma)
        self._lemmas = sorted(lemmas, key=lambda k: (k.sort_key, k.volume.sort_key))

    def _is_lemma_of_author(self, lemma: Lemma) -> bool:
        for chapter in lemma.chapters:
            if chapter.author:
                authors_of_lemma = self._authors.get_author_by_mapping(chapter.author, lemma.volume.name)
                if self._author in authors_of_lemma:
                    return True
        return False

    def _get_table(self) -> str:
        header = """{|class="wikitable sortable"
!Artikel
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
            if chapter_sum > 1:
                table.append(f"|-\n|rowspan={chapter_sum} data-sort-value=\"{lemma.sort_key}\"|{lemma.get_link()}")
            else:
                table.append(f"|-\n|data-sort-value=\"{lemma.sort_key}\"|{lemma.get_link()}")
            table += table_rows
        table.append("|}")
        return "\n".join(table)

    def _get_header(self) -> str:
        header = ["RERegister"]
        header.append(f"AUTHOR={self._author.name}")
        header.append(f"SUM={len(self)}")
        # calculate proof_read status
        fer, kor, unk = self.proof_read
        header.append(f"UNK={unk}")
        header.append(f"KOR={kor}")
        header.append(f"FER={fer}")
        return "{{" + "\n|".join(header) + "\n}}\n"

    def _get_footer(self) -> str:
        return f"[[Kategorie:RE:Register|{self.author.last_name}, {self.author.first_name}]]"

    def get_register_str(self) -> str:
        return f"{self._get_header()}\n{self._get_table()}\n{self._get_footer()}"

    @property
    def overview_line(self):
        line = ["|-\n", f"|data-sort-value=\"{self.author.last_name}, {self.author.first_name}\""]
        line.append(f"|[[Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/"
                    f"{self.author.name}|{self.author.name}]]\n")
        line.append(f"|data-sort-value=\"{len(self):04d}\"|{len(self)}\n")
        fer, kor, _ = self.proof_read
        parts_fertig, parts_korrigiert, parts_unkorrigiert = self.proofread_parts_of_20(len(self), fer, kor)
        line.append("|data-sort-value=\"{percent:05.1f}\"|{percent:.1f}%\n"
                    .format(percent=((fer + kor) / len(self)) * 100))
        line.append(f"|<span style=\"color:#669966\">{parts_fertig * '█'}</span>")
        line.append(f"<span style=\"color:#556B2F\">{parts_korrigiert * '█'}</span>")
        line.append(f"<span style=\"color:#AA0000\">{parts_unkorrigiert * '█'}</span>")
        return "".join(line)

    @staticmethod
    def proofread_parts_of_20(sum_lemmas: int, fer: int, kor: int) -> Tuple[int, int, int]:
        part_fer = round(fer / sum_lemmas * 20)
        part_kor = round((kor + fer) / sum_lemmas * 20) - part_fer
        part_unk = 20 - (part_fer + part_kor)
        return part_fer, part_kor, part_unk
