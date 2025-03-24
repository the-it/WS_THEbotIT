# pylint: disable=protected-access,no-self-use

from testfixtures import compare

from service.ws_re.register.registers import Registers
from service.ws_re.register.repo import DataRepo
from service.ws_re.register.test_base import BaseTestRegister, copy_tst_data
from service.ws_re.volumes import Volumes


class TestRegisters(BaseTestRegister):
    def test_init(self):
        for volume in Volumes().all_volumes:
            copy_tst_data("I_1_base", volume.file_name)
        registers = Registers()
        iterator = iter(registers.volumes.values())
        compare("I,1", next(iterator).volume.name)
        for _ in range(83):
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
        i = 0
        for i, register in enumerate(Registers().alphabetic):
            if register.start == "a":
                compare(4, len(register))
                continue
            if register.start == "b":
                compare(2, len(register))
                continue
            if register.start == "ch":
                compare(1, len(register))
                continue
            if register.start == "d":
                compare(1, len(register))
                continue
            if register.start == "u":
                compare(2, len(register))
                continue
        compare(43, i)

    def test_author(self):
        copy_tst_data("I_1_author", "I_1")
        copy_tst_data("III_1_author", "III_1")
        author_registers = iter(Registers().author)
        register = next(author_registers)
        compare("Herman Abel", register.author.name)
        compare(4, len(register))
        register = next(author_registers)
        compare("Abert", register.author.name)
        compare(5, len(register))
        register = next(author_registers)
        compare("William Abbott", register.author.name)
        compare(2, len(register))

    def test_persist(self):
        copy_tst_data("I_1_alpha", "I_1")
        copy_tst_data("III_1_alpha", "III_1")
        registers = Registers()
        register_I_1 = registers["I,1"]
        register_I_1._lemmas[0]._chapters[0].author = "Siegfried"
        register_III_1 = registers["III,1"]
        register_III_1._lemmas[0]._chapters[0].author = "Siegfried"
        registers.persist()
        with open(DataRepo.get_data_path().joinpath("I_1.json"), mode="r", encoding="utf-8") as register_file:
            self.assertTrue("Siegfried" in register_file.read())
        with open(DataRepo.get_data_path().joinpath("III_1.json"), mode="r", encoding="utf-8") as register_file:
            self.assertTrue("Siegfried" in register_file.read())
