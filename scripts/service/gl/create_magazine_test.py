from scripts.service.gl.create_magazine import search_for_refs
from test import *


@ddt
class TestSearchForRefs(TestCase):
    @file_data("scan_for_refs.json")
    def test_data_provider(self, value):
        for item in value:
            self.assertEqual(item[1], search_for_refs(item[0]),
                             "\"{}\" should convert to \"{}\"".format(item[0], item[1]))
