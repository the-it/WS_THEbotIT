from unittest import TestCase

from ddt import ddt, file_data
from testfixtures import compare

from service.list_bots._base import get_page_infos, is_empty_value


@ddt
class Test(TestCase):
    @file_data("test_data/test_get_page_infos.yml")
    def test_get_page_infos(self, given, expect):
        compare(expect, get_page_infos(given["text"], given["name"], given["mapping"]))

    def test_get_page_infos_errors(self):
        with self.assertRaises(ValueError):
            get_page_infos("", "Personendaten", {})
        with self.assertRaises(ValueError):
            get_page_infos("{{Personendaten", "Personendaten", {})
        with self.assertRaises(ValueError):
            get_page_infos("{{Personendaten}}\n{{Personendaten}}", "Personendaten", {})

    def test_is_empty_value(self):
        compare(True, is_empty_value("key", {"other_key": "1"}))
        compare(True, is_empty_value("key", {"key": ""}))
        compare(False, is_empty_value("key", {"key": "1"}))
