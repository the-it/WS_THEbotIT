from test import *
from tools.date_conversion import DateConversion


@ddt
class TestDateConversion(TestCase):
    @file_data("date_conversion.json")
    def test_data_provider(self, value):
        for item in value:
            converter = DateConversion(item[0])
            self.assertEqual(item[1], str(converter), "\"{}\" should convert to \"{}\"".format(item[0], item[1]))
            del converter
