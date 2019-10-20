# pylint: disable=protected-access
from datetime import datetime
from unittest import TestCase

from testfixtures import compare

from scripts.service.gl.status import GlStatus


class TestGlStatus(TestCase):
    @staticmethod
    def test_projektstand():
        given_file = """aaa
<!--new line: Liste wird von einem Bot aktuell gehalten.-->
bbb"""
        result = """aaa
<!--new line: Liste wird von einem Bot aktuell gehalten.-->
|-
|01.01.2000|| 50000 || 25000 (50,00 %) || 15000 (30,00 %) || 10000 (20,00 %) || 9250/18500 (50,00 %) ||
bbb"""
        bot = GlStatus(None, False)
        bot.timestamp._start = datetime(year=2000, month=1, day=1)
        compare(result, bot.projektstand(temp_text=given_file, alle=50000, fertig=10000,
                                         korrigiert=15000, unkorrigiert=25000, articles=9250))

    @staticmethod
    def test_to_percent():
        test_array = (((0, 1), " (0,00 %)"),
                      ((1, 4), " (25,00 %)"),
                      ((1, 3), " (33,33 %)"),
                      ((2, 3), " (66,67 %)"),
                      ((3, 3), " (100,00 %)"))

        bot = GlStatus(None, False)
        for pair in test_array:
            compare(pair[1], bot.to_percent(*pair[0]))
