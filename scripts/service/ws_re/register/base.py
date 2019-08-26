from abc import ABC
from pathlib import Path

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
                else:
                    return_lemmas.append(last_lemmas)
                    last_lemmas = []
            last_lemmas.append(lemma)
        if last_lemmas:
            return_lemmas.append(last_lemmas)
        return return_lemmas
