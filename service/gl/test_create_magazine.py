from unittest import TestCase

from ddt import ddt, file_data

from service.gl.create_magazine import search_for_refs


@ddt
class TestSearchForRefs(TestCase):
    @file_data("scan_for_refs.json")
    def test_data_provider(self, value):
        for item in value:
            self.assertEqual(item[1], search_for_refs(item[0]),
                             f"\"{item[0]}\" should convert to \"{item[1]}\"")
