# pylint: disable=protected-access,no-self-use
from unittest import TestCase

from ddt import ddt, file_data
from testfixtures import compare

from service.ws_re.register.importer import ReImporter


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
        tm_set = ReImporter._load_tm_set()
        self.assertTrue("Hermogenes 27" in tm_set)
