from unittest import TestCase

from ddt import ddt, file_data
from testfixtures import compare

from tools.date_conversion import DateConversion


@ddt
class TestDateConversion(TestCase):
    @file_data("test_date_conversion.json")
    def test_data_provider(self, value):
        for item in value:
            converter = DateConversion(item[0])
            compare(expected=item[1], actual=str(converter))
            del converter
