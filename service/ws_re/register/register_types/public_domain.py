from typing import Dict, List

from service.ws_re.register._base import Register
from service.ws_re.register.author import Author
from service.ws_re.register.authors import Authors
from service.ws_re.register.lemma import Lemma
from service.ws_re.register.register_types.volume import VolumeRegister


class PublicDomainRegister(Register):
    def __init__(self,
                 year: int,
                 authors: Authors,
                 registers: Dict[str, VolumeRegister]):
        self.year: int = year
        self._authors: Authors = authors
        self._registers = registers
        self._lemmas: List[Lemma] = []
        self._pd_authors: List[Author] = self._get_pd_authors()
        self._init_lemmas()

    def __repr__(self):
        return f"<{self.__class__.__name__} - year:{self.year}, lemmas:{len(self)}>"

    def __len__(self):
        return len(self.squash_lemmas(self._lemmas))

    def __getitem__(self, item: int) -> Lemma:
        return self._lemmas[item]

    def _init_lemmas(self):
        lemmas = []
        for volume_str in self._registers:
            for lemma in self._registers[volume_str].lemmas:
                if self._is_lemma_of_author(lemma):
                    lemmas.append(lemma)
        self._lemmas = sorted(lemmas, key=lambda k: (k.sort_key, k.volume.sort_key))

    def _get_pd_authors(self) -> List[Author]:
        author_list = []
        for author in self._authors:
            if author.death:
                if author.death == self.year - 71:
                    author_list.append(author)
                continue
            if author.birth == self.year - 171:
                author_list.append(author)
        return author_list

    def _is_lemma_of_author(self, lemma: Lemma) -> bool:
        for chapter in lemma.chapters:
            if chapter.author:
                authors_of_lemma = self._authors.get_author_by_mapping(chapter.author, lemma.volume.name)
                for author in self._pd_authors:
                    if author in authors_of_lemma:
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

    def _get_footer(self) -> str:
        return f"Zahl der Artikel: {len(self._lemmas)}, "

    def get_register_str(self) -> str:
        return f"{self._get_table()}\n{self._get_footer()}"
