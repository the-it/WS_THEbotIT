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
        copy_tst_data("I_1_alpha", "II_1")
        copy_tst_data("III_1_alpha", "II_2")
        self.authors = Authors()
        self.volumes = Volumes()
        self.registers = OrderedDict()
        self.registers["II,1"] = VolumeRegister(self.volumes["II,1"], self.authors)
        self.registers["II,2"] = VolumeRegister(self.volumes["II,2"], self.authors)

    def test_init(self):
        i_register = ShortRegister("I", self.registers)
        ii_register = ShortRegister("II", self.registers)
        compare(11, len(ii_register))
        compare(0, len(i_register))

    def test_make_table(self):
        ii_register = ShortRegister("II", self.registers)
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
        compare(expected_table, ii_register.get_register_str())
