from typing import Dict, List

from service.ws_re import public_domain
from service.ws_re.register.author import Author
from service.ws_re.register.authors import Authors
from service.ws_re.register.lemma import Lemma
from service.ws_re.register.register_types._base import Register
from service.ws_re.register.register_types.volume import VolumeRegister


class PublicDomainRegister(Register):
    def __init__(self,
                 year: int,
                 authors: Authors,
                 registers: Dict[str, VolumeRegister]):
        super().__init__()
        self._registers = registers
        self.year: int = year
        self._authors: Authors = authors
        self._pd_authors: List[Author] = self._get_pd_authors()
        self._init_lemmas(self._is_lemma_of_author)

    def __repr__(self):
        return f"<{self.__class__.__name__} - year:{self.year}, lemmas:{len(self)}>"

    def __len__(self):
        return len(self.squash_lemmas(self._lemmas))

    def __getitem__(self, item: int) -> Lemma:
        return self._lemmas[item]

    def _get_pd_authors(self) -> List[Author]:
        author_list = []
        for author in self._authors:
            if author.death:
                if author.death == self.year - public_domain.YEARS_AFTER_DEATH:
                    author_list.append(author)
                continue
            if author.birth == self.year - public_domain.YEARS_AFTER_BIRTH:
                author_list.append(author)
        return author_list

    def _is_lemma_of_author(self, lemma: Lemma) -> bool:
        for chapter in lemma.chapter_objects:
            if chapter.author:
                authors_of_lemma = self._authors.get_author_by_mapping(chapter.author, lemma.volume.name)
                for author in self._pd_authors:
                    if author in authors_of_lemma:
                        return True
        return False

    def get_register_str(self) -> str:
        return f"{self._get_table()}\n[[Kategorie:RE:Register|!]]"
