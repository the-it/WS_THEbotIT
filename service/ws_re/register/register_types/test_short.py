# pylint: disable=protected-access
from collections import OrderedDict

from testfixtures import compare

from service.ws_re.register.authors import Authors
from service.ws_re.register.register_types.short import ShortRegister
from service.ws_re.register.register_types.volume import VolumeRegister
from service.ws_re.register.test_base import BaseTestRegister, copy_tst_data
from service.ws_re.volumes import Volumes


class TestShortRegister(BaseTestRegister):
    def setUp(self):
        copy_tst_data("I_1_alpha", "I_1")
        copy_tst_data("III_1_alpha", "I_2")
        self.authors = Authors()
        self.volumes = Volumes()
        self.registers = OrderedDict()
        self.registers["I,1"] = VolumeRegister(self.volumes["I,1"], self.authors)
        self.registers["I,2"] = VolumeRegister(self.volumes["I,2"], self.authors)

    def test_init(self):
        i_register = ShortRegister("I", self.registers)
        compare(10, len(i_register))

    def test_make_table(self):
        i_register = ShortRegister("I", self.registers)
        expected_table = """[[RE:Aal|Aal]] |
[[RE:Aba 1|Aba 1]] |
[[RE:Aba 2|Aba 2]] |
[[RE:Adam|Adam]] |
[[RE:Baaba|Baaba]] |
[[RE:Beta|Beta]] |
[[RE:Charlie|Charlie]] |
[[RE:Delta|Delta]] |
[[RE:Vaaa|Vaaa]] |
[[RE:Ueee|Ueee]]"""
        compare(expected_table, i_register.get_register_str())
