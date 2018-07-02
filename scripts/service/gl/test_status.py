from datetime import datetime

from scripts.service.gl.status import GlStatus
from test import *

class TestGlStatus(TestCase):
    def test_projektstand(self):
        given_file = """aaa
<!--new line: Liste wird von einem Bot aktuell gehalten.-->
bbb"""
        result = """aaa
<!--new line: Liste wird von einem Bot aktuell gehalten.-->
|-
|01.01.2000|| 40000 || 10000 (25,00 %) || 10000 (25,00 %) || 20000 (50,00 %) || 9250/18500 (50,00 %) ||
bbb"""
        bot = GlStatus(None, False)
        bot.timestamp._start = datetime(year=2000, month=1, day=1)
        compare(result, bot.projektstand(given_file, 40000, 10000, 10000, 20000, 9250))