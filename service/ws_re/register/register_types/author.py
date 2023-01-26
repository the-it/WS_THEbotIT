from typing import Dict, Tuple

from service.ws_re.register.author import Author
from service.ws_re.register.authors import Authors
from service.ws_re.register.lemma import Lemma
from service.ws_re.register.register_types._base import Register
from service.ws_re.register.register_types.volume import VolumeRegister


class AuthorRegister(Register):
    def __init__(self,
                 author: Author,
                 authors: Authors,
                 registers: Dict[str, VolumeRegister]):
        super().__init__()
        self._registers = registers
        self._author: Author = author
        self._authors: Authors = authors
        self._init_lemmas(self._is_lemma_of_author)

    def __repr__(self):
        return f"<{self.__class__.__name__} - author:{self._author}, lemmas:{len(self)}>"

    def __len__(self):
        return len(self._lemmas)

    def __getitem__(self, item: int) -> Lemma:
        return self._lemmas[item]

    @property
    def author(self):
        return self._author

    def _is_lemma_of_author(self, lemma: Lemma) -> bool:
        for chapter in lemma.chapters:
            if chapter.author:
                authors_of_lemma = self._authors.get_author_by_mapping(chapter.author, lemma.volume.name)
                if self._author in authors_of_lemma:
                    return True
        return False

    def _get_header(self) -> str:
        header = ["RERegister"]
        header.append(f"AUTHOR={self._author.name}")
        header.append(f"SUM={len(self)}")
        # calculate proof_read status
        fer, kor, nge, vor, unk = self.proof_read
        header.append(f"FER={fer}")
        header.append(f"KOR={kor}")
        header.append(f"NGE={nge}")
        header.append(f"VOR={vor}")
        header.append(f"UNK={unk}")
        return "{{" + "\n|".join(header) + "\n}}\n"

    def _get_footer(self) -> str:
        return f"[[Kategorie:RE:Register|{self.author.last_name}, {self.author.first_name}]]"

    def get_register_str(self, print_details: bool = True) -> str:
        return f"{self._get_header()}" \
               f"\n{self._get_table(print_description=print_details, print_author=print_details)}" \
               f"\n{self._get_footer()}"

    @property
    def overview_line(self):
        line = ["|-\n", f"|data-sort-value=\"{self.author.last_name}, {self.author.first_name}\""]
        line.append(f"|[[Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/"
                    f"{self.author.name}|{self.author.name}]]\n")
        line.append(f"|data-sort-value=\"{len(self):04d}\"|{len(self)}\n")
        fer, kor, nge, vor, _ = self.proof_read
        parts_fertig, parts_korrigiert, parts_nicht_gemeinfrei, parts_vorbereitet, parts_unkorrigiert = \
            self.proofread_parts_of_20(len(self), fer, kor, nge, vor)
        line.append("|data-sort-value=\"{percent:05.1f}\"|{percent:.1f}%\n"
                    .format(percent=((fer + kor) / len(self)) * 100))
        line.append(f"|<span style=\"color:#669966\">{parts_fertig * '█'}</span>")
        line.append(f"<span style=\"color:#556B2F\">{parts_korrigiert * '█'}</span>")
        line.append(f"<span style=\"color:#FFCBCB\">{parts_nicht_gemeinfrei * '█'}</span>")
        line.append(f"<span style=\"color:#9FC859\">{parts_vorbereitet * '█'}</span>")
        line.append(f"<span style=\"color:#AA0000\">{parts_unkorrigiert * '█'}</span>")
        return "".join(line)

    @staticmethod
    def proofread_parts_of_20(sum_lemmas: int, fer: int, kor: int, nge: int, vor: int) \
            -> Tuple[int, int, int, int, int]:
        part_fer = round(fer / sum_lemmas * 20)
        part_kor = round((kor + fer) / sum_lemmas * 20) - part_fer
        part_nge = round((kor + fer + nge) / sum_lemmas * 20) - (part_fer + part_kor)
        part_vor = round((kor + fer + nge + vor) / sum_lemmas * 20) - (part_fer + part_kor + part_nge)
        part_unk = 20 - (part_fer + part_kor + part_nge + part_vor)
        return part_fer, part_kor, part_nge, part_vor, part_unk
