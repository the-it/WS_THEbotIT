import time
from unittest import skipUnless, TestCase, skip

from testfixtures import compare

from scripts.service.ws_re.register.registers import Registers
from scripts.service.ws_re.register.test_base import BaseTestRegister, copy_tst_data, \
    _TEST_REGISTER_PATH
from scripts.service.ws_re.volumes import Volumes
from tools import INTEGRATION_TEST


class TestRegisters(BaseTestRegister):
    def test_init(self):
        for volume in Volumes().all_volumes:
            copy_tst_data("I_1_base", volume.file_name)
        registers = Registers()
        iterator = iter(registers.volumes.values())
        compare("I,1", next(iterator).volume.name)
        for i in range(83):
            last = next(iterator)
        compare("R", last.volume.name)
        compare(84, len(registers.volumes))
        compare("IV,1", registers["IV,1"].volume.name)

    def test_not_all_there(self):
        copy_tst_data("I_1_base", "I_1")
        Registers()

    def test_alphabetic(self):
        copy_tst_data("I_1_alpha", "I_1")
        copy_tst_data("III_1_alpha", "III_1")
        registers = Registers()
        compare(44, len(registers.alphabetic))
        compare(4, len(registers.alphabetic["a"]))
        compare(2, len(registers.alphabetic["b"]))
        compare(1, len(registers.alphabetic["ch"]))
        compare(1, len(registers.alphabetic["d"]))
        compare(2, len(registers.alphabetic["u"]))

    def test_alphabetic_persist(self):
        copy_tst_data("I_1_alpha", "I_1")
        copy_tst_data("III_1_alpha", "III_1")
        registers = Registers()
        register_I_1 = registers["I,1"]
        register_I_1._lemmas[0]._chapters[0]._dict["author"] = "Siegfried"
        register_III_1 = registers["III,1"]
        register_III_1._lemmas[0]._chapters[0]._dict["author"] = "Siegfried"
        registers.persist()
        with open(_TEST_REGISTER_PATH.joinpath("I_1.json"), mode="r") as register_file:
            self.assertTrue("Siegfried" in register_file.read())
        with open(_TEST_REGISTER_PATH.joinpath("III_1.json"), mode="r") as register_file:
            self.assertTrue("Siegfried" in register_file.read())


_MAX_SIZE_WIKI_PAGE = 2_098_175


@skipUnless(INTEGRATION_TEST, "only execute in integration test")
class TestIntegrationRegister(TestCase):
    @classmethod
    def setUpClass(cls):
        start = time.time()
        cls.registers = Registers()
        end = time.time()
        init_time = end - start
        if init_time > 15:
            raise AssertionError(f"Register take to long to initiate ... {init_time} s. "
                                 "It should initiate in 15 seconds.")

    def test_length_of_alphabetic(self):
        for register in self.registers.alphabetic.values():
            self.assertGreater(_MAX_SIZE_WIKI_PAGE, len(register.get_register_str()), f"register {register} is now to big.")

    def test_previous_next_in_order(self):
        errors = []
        for register in self.registers.volumes.values():
            for i, lemma in enumerate(register):
                pre_lemma = register[i -1] if i > 0 else None
                if pre_lemma and pre_lemma["next"]:
                    if not pre_lemma["next"] == lemma["lemma"]:  # pragma: no cover
                        errors.append(f"PRE lemma name {lemma['lemma']} /{i} in register {register.volume.name} not the same as pre lemma")
                try:
                    post_lemma = register[i + 1]
                    if post_lemma and post_lemma["previous"]:
                        if not post_lemma["previous"] == lemma["lemma"]:  # pragma: no cover
                            errors.append(f"POST lemma name {lemma['lemma']} /{i} in register {register.volume.name} not the same as post lemma")
                except IndexError:
                    pass

        if errors:  # pragma: no cover
            count = len(errors)
            errors.insert(0, f"COUNT ERRORS: {count}")
            errors.append(f"COUNT ERRORS: {count}")
            raise AssertionError("\n".join(errors))

    @skip("not fully implemented yet")
    def test_previous_double_lemmas(self):
        LEMMA_DISTANCE = 80
        errors = []
        for register in self.registers.volumes.values():
            lemmas = dict()
            for i, lemma in enumerate(register):
                lemma = lemma["lemma"]
                if lemma not in lemmas:
                    lemmas[lemma] = i
                else:
                    if i - lemmas[lemma] < LEMMA_DISTANCE:  # pragma: no cover
                        errors.append(f"distance problem {register.volume.name}, {lemma}, {lemmas[lemma]}, {i}")
                    lemmas[lemma] = i
        if errors:  # pragma: no cover
            count = len(errors)
            errors.insert(0, f"COUNT ERRORS: {count}")
            errors.append(f"COUNT ERRORS: {count}")
            raise AssertionError("\n".join(errors))

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
        for i in range(len(lemma_1)):
            if lemma_1[i] != lemma_2[i]:
                raise AssertionError(f"position {i} {lemma_1[i]}({ord(lemma_1[i])}) != {lemma_2[i]}({ord(lemma_2[i])})")
