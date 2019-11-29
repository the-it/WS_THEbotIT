# pylint: disable=protected-access,no-self-use
from testfixtures import compare

from scripts.service.ws_re.register.registers import Registers
from scripts.service.ws_re.register.test_base import BaseTestRegister, copy_tst_data, \
    _TEST_REGISTER_PATH
from scripts.service.ws_re.volumes import Volumes


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
        registers = Registers()
        compare(44, len(registers.alphabetic))
        compare(4, len(registers.alphabetic["a"]))
        compare(2, len(registers.alphabetic["b"]))
        compare(1, len(registers.alphabetic["ch"]))
        compare(1, len(registers.alphabetic["d"]))
        compare(2, len(registers.alphabetic["u"]))

    def test_author(self):
        copy_tst_data("I_1_author", "I_1")
        copy_tst_data("III_1_author", "III_1")
        author_registers = iter(Registers().author)
        register = next(author_registers)
        compare("Abbott", register.author.name)
        compare(2, len(register))
        register = next(author_registers)
        compare("Abel", register.author.name)
        compare(4, len(register))
        register = next(author_registers)
        compare("Abert", register.author.name)
        compare(5, len(register))

    def test_persist(self):
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
