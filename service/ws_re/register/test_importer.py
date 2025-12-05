# pylint: disable=protected-access,no-self-use
from unittest import TestCase

from ddt import ddt, file_data
from testfixtures import compare

from service.ws_re.register.importer import ReImporter
from service.ws_re.register.registers import Registers
from tools.test import real_wiki_test


@ddt
class TestReImporter(TestCase):
    @staticmethod
    def test_get_author_mapping():
        mapping = ReImporter.get_author_mapping()
        compare("Stein.", mapping["Arthur Stein"])
        compare("A.W.", mapping["Albert Wünsch"])
        compare("A. E. Gordon.", mapping["Arthur Ernest Gordon"])

    @file_data("test_data/test_importer.yml")
    def test_adjust_author(self, given, expect):
        mapping = ReImporter.get_author_mapping()
        compare(expect, ReImporter.adjust_author(given, mapping))

    def test_load_tm_list(self):
        tm_set = ReImporter.load_tm_set()
        self.assertTrue("Hermogenes 27" in tm_set)

    @real_wiki_test
    def test_adjust_end_column(self):
        registers = Registers()
        register = registers["XVI,1"]
        for idx, article in enumerate(register):
            if article.lemma == "Molorchos":
                #start test
                pre_1 = """{{REDaten
|BAND=XVI,1
|SPALTE_START=13
|SPALTE_END=OFF
|VORGÄNGER=Molorchia
|NACHFOLGER=Μόλος 1
}}
'''Molorchos'''
[...]
{{REAutor|J. Pley.}}"""
                self.assertTrue("SPALTE_END=14" in ReImporter.adjust_end_column(pre_1, register, idx))
                pre_2 = """{{REDaten
|BAND=XVI,1
|SPALTE_START=12
|SPALTE_END=OFF
|VORGÄNGER=Molorchia
|NACHFOLGER=Μόλος 1
}}
'''Molorchos'''
[...]
{{REAutor|J. Pley.}}"""
                # not clear don't do shit
                self.assertTrue("SPALTE_END=OFF" in ReImporter.adjust_end_column(pre_2, register, idx))
                # index out of range
                self.assertTrue("SPALTE_END=OFF" in ReImporter.adjust_end_column(pre_2, register, 9999))
                pre_3 = """{{REDaten
|BAND=XVI,1
|SPALTE_START=nothing
|SPALTE_END=OFF
|VORGÄNGER=Molorchia
|NACHFOLGER=Μόλος 1
}}
'''Molorchos'''
[...]
{{REAutor|J. Pley.}}"""
                # can't determine start column
                self.assertTrue("SPALTE_END=OFF" in ReImporter.adjust_end_column(pre_3, register, idx))
                pre_4 = """{{REDaten
|BAND=XVI,1
|SPALTE_START=14
|SPALTE_END=OFF
|VORGÄNGER=Molorchia
|NACHFOLGER=Μόλος 1
}}
'''Molorchos'''
[...]
{{REAutor|J. Pley.}}"""
                # start on the same column like follow article
                self.assertTrue("SPALTE_END=OFF" in ReImporter.adjust_end_column(pre_4, register, idx))
