from abc import ABC
from pathlib import Path
from typing import Tuple

_REGISTER_PATH = Path(__file__).parent.joinpath("data")


class RegisterException(Exception):
    pass


class Register(ABC):
    @staticmethod
    def squash_lemmas(lemmas):
        return_lemmas = []
        last_lemmas = []
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

    @staticmethod
    def proof_read(lemmas) -> Tuple[int, int, int]:
        fer = kor = unk = 0
        for lemma in lemmas:
            proof_read = lemma["proof_read"]
            if proof_read:
                if proof_read == 3:
                    fer += 1
                elif proof_read == 2:
                    kor += 1
                elif proof_read == 1:
                    unk += 1
        return fer, kor, unk
