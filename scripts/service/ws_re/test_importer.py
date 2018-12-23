from unittest import TestCase

from testfixtures import compare

from scripts.service.ws_re.importer import ReImporter


class TestReImporter(TestCase):
    def setUp(self):
        self.re_importer = ReImporter(log_to_screen=False, log_to_wiki=False, debug=False)

    def test_split_line(self):
        line = """|[[RE:Herodes 14]]{{Anker|Herodes 14}}
|[[Special:Filepath/Pauly-Wissowa_S_II,_0001.jpg|S II, 1]] : [http://www.archive.org/download/PWRE68/Pauly-Wissowa_S_II_0001.png IA]-158
|Otto, Walter
|1941"""
        result = self.re_importer._split_line(line)
        expectation = ["[[RE:Herodes 14]]{{Anker|Herodes 14}}",
                       "[[Special:Filepath/Pauly-Wissowa_S_II,_0001.jpg|S II, 1]] : [http://www.archive.org/download/PWRE68/Pauly-Wissowa_S_II_0001.png IA]-158",
                       "Otto, Walter",
                       "1941"]
        compare(expectation, result)
        result = self.re_importer._split_line(line[1:]) # no | at start is good too
        compare(expectation, result)

    def test_split_table(self):
        table = """{|
|-
|1
|2
|3
|4
|-
|5
|6
|7
|8
|-
|1
|2
|3
|4
|-
|5
|6
|7
|8
|}
[[Kategorie:RE:Register|!]]
Zahl der Artikel: 15, davon [[:Kategorie:RE:Band S II|{{PAGESINCATEGORY:RE:Band S II|pages}} in Volltext]].
"""
        result = self.re_importer._split_table(table)
        expectation = ["|1\n|2\n|3\n|4",
                       "|5\n|6\n|7\n|8",
                       "|1\n|2\n|3\n|4",
                       "|5\n|6\n|7\n|8"]
        compare(expectation, result)
