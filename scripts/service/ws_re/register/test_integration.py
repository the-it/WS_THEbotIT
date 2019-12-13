# pylint: disable=no-self-use,protected-access
import contextlib
from unittest import skipUnless, TestCase, skip

from pyfiglet import Figlet

from scripts.service.ws_re.register.authors import Authors
from scripts.service.ws_re.register.registers import Registers
from scripts.service.ws_re.register.test_base import BaseTestRegister
from tools import INTEGRATION_TEST

_MAX_SIZE_WIKI_PAGE = 2_098_175

def _raise_count_errors(errors):
    if errors:  # pragma: no cover
        count = len(errors)
        banner = "\n" + Figlet(font="big").renderText(f"ERRORS: {count}")
        errors.insert(0, banner)
        errors.append(banner)
        raise AssertionError("\n".join(errors))


if INTEGRATION_TEST:
    parent_class = TestCase
else:
    parent_class = BaseTestRegister # type: ignore


@skipUnless(INTEGRATION_TEST, "only execute in integration test")
class TestAuthors(parent_class):
    @classmethod
    def setUpClass(cls) -> None:
        cls.authors = Authors()  # type: ignore

    def test_all_mappings_have_target(self):
        errors = []
        authors_in_mappings = set()
        for mapping in self.authors._mapping.values():
            if isinstance(mapping, str):
                authors_in_mappings.add(mapping)
            elif isinstance(mapping, list):
                for author in mapping:
                    authors_in_mappings.add(author)
            else:
                for author in mapping.values():
                    authors_in_mappings.add(author)
        for author in authors_in_mappings:
            try:
                self.authors.get_author(author)
            except KeyError:  # pragma: no cover
                errors.append(f"Mapping target {author} not there.")
        _raise_count_errors(errors)


@skipUnless(INTEGRATION_TEST, "only execute in integration test")
class TestIntegrationRegister(parent_class):
    @classmethod
    def setUpClass(cls):
        cls.registers = Registers()

    def test_length_of_alphabetic(self):
        for register in self.registers.alphabetic:
            self.assertGreater(_MAX_SIZE_WIKI_PAGE, len(register.get_register_str()),
                               f"register {register} is now to big.")

    def test_previous_next_in_order(self):
        errors = []
        for register in self.registers.volumes.values():
            for i, lemma in enumerate(register):
                pre_lemma = register[i -1] if i > 0 else None
                if pre_lemma and pre_lemma["next"]:
                    if not pre_lemma["next"] == lemma["lemma"]:  # pragma: no cover
                        errors.append(f"PRE lemma name {lemma['lemma']} /{i} in register {register.volume.name} "
                                      f"not the same as pre lemma")
                with contextlib.suppress(IndexError):
                    post_lemma = register[i + 1]
                    if post_lemma and post_lemma["previous"]:
                        if not post_lemma["previous"] == lemma["lemma"]:  # pragma: no cover
                            errors.append(f"POST lemma name {lemma['lemma']} /{i} in register {register.volume.name} "
                                          f"not the same as post lemma")
        _raise_count_errors(errors)

    _DOUBLE_LEMMAS = {"Orpheus 1", "Victor 69"}

    def test_previous_double_lemmas(self):
        LEMMA_DISTANCE = 40
        errors = []
        for register in self.registers.volumes.values():
            lemmas = dict()
            for i, lemma in enumerate(register):
                lemma = lemma["lemma"]
                if lemma not in lemmas:
                    lemmas[lemma] = i
                else:
                    if i - lemmas[lemma] < LEMMA_DISTANCE:  # pragma: no cover
                        if lemma not in self._DOUBLE_LEMMAS:
                            errors.append(f"distance problem {register.volume.name}, {lemma} , {lemmas[lemma]}, {i}")
                    lemmas[lemma] = i
        _raise_count_errors(errors)

    def test_all_authors_has_a_target_in_mapping(self):
        errors = []
        mappings = set(self.registers.authors._mapping.keys())
        for register in self.registers.volumes.values():
            for lemma in register:
                for chapter in lemma.chapters:
                    if chapter.author and chapter.author not in mappings:  # pragma: no cover
                        errors.append(f"Author {chapter.author}, {lemma['lemma']}, "
                                      f"{register.volume.name} not in mappings.")
        _raise_count_errors(errors)

    @skip("only for analysis")
    def test_no_double_lemma(self):  # pragma: no cover
        for register in self.registers.volumes.values():
            unique_lemmas = set()
            for lemma in register.lemmas:
                lemma_name = lemma["lemma"]
                if lemma_name in unique_lemmas:
                    print(f"Lemma {lemma_name} is not unique in register {register.volume.name}")
                unique_lemmas.add(lemma_name)


@skip("only for analysis")
class TestAnalyse(TestCase):
    def test_compare_lemma(self):  # pragma: no cover
        lemma_1 = "lemma 1"
        lemma_2 = "lemma 1"
        for i, _ in enumerate(lemma_1):
            if lemma_1[i] != lemma_2[i]:
                raise AssertionError(f"position {i} {lemma_1[i]}({ord(lemma_1[i])}) "
                                     f"!= {lemma_2[i]}({ord(lemma_2[i])})")
