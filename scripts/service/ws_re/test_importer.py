import os
import shutil
from pathlib import Path
from unittest import TestCase

from testfixtures import compare, LogCapture

from scripts.service.ws_re.importer import ReImporter


class TestReImporter(TestCase):
    @classmethod
    def setUpClass(cls):
        shutil.rmtree(Path(__file__).parent.joinpath("test_register"))
        os.mkdir(Path(__file__).parent.joinpath("test_register"))

    def setUp(self):
        self.re_importer = ReImporter(log_to_screen=False, log_to_wiki=False, debug=False)
        self.re_importer._register_folder = "test_register"


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
        result = self.re_importer._split_line(line[1:])  # no | at start is good too
        compare(expectation, result)

    def test_split_line_too_much_content(self):
        line = """|[[RE:Herodes 14]]{{Anker|Herodes 14}}
|[[Special:Filepath/Pauly-Wissowa_S_II,_0001.jpg|S II, 1]] : [http://www.archive.org/download/PWRE68/Pauly-Wissowa_S_II_0001.png IA]-158
|Otto, Walter
|1941
|bla"""
        with LogCapture():
            with self.assertRaises(ValueError):
                result = self.re_importer._split_line(line)


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

    def test_split_table_bug_1(self):
        table = """{|
|-
|[[RE:uslan]]{{Anker|uslan}}
|[[Special:Filepath/Pauly-Wissowa_IX_A,1,_1091.jpg|IX A,1, 1091]] : [[:wikilivres:Special:Filepath/Pauly-Wissowa_IX_A,1,_1091.png|WL]]
|Enking
|1975
|-
|[[RE:-usnehae]]{{Anker|-usnehae}}
|[[Special:Filepath/Pauly-Wissowa_IX_A,1,_1091.jpg|IX A,1, 1091]] : [[:wikilivres:Special:Filepath/Pauly-Wissowa_IX_A,1,_1091.png|WL]]-1092
|Heichelheim
|1968
|}
[[Kategorie:RE:Register|!]]
Zahl der Artikel: 15, davon [[:Kategorie:RE:Band S II|{{PAGESINCATEGORY:RE:Band S II|pages}} in Volltext]].
"""
        result = self.re_importer._split_table(table)
        expectation = ["|[[RE:uslan]]{{Anker|uslan}}\n|[[Special:Filepath/Pauly-Wissowa_IX_A,1,_1091.jpg|IX A,1, 1091]] : [[:wikilivres:Special:Filepath/Pauly-Wissowa_IX_A,1,_1091.png|WL]]\n|Enking\n|1975",
                       "|[[RE:-usnehae]]{{Anker|-usnehae}}\n|[[Special:Filepath/Pauly-Wissowa_IX_A,1,_1091.jpg|IX A,1, 1091]] : [[:wikilivres:Special:Filepath/Pauly-Wissowa_IX_A,1,_1091.png|WL]]-1092\n|Heichelheim\n|1968"]
        compare(expectation, result)

    def test_first_column(self):
        content = "[[RE:Herodes 14]]{{Anker|Herodes 14}}"
        result = self.re_importer._analyse_first_column(content)
        compare({"lemma": "Herodes 14"}, result)

    def test_second_column(self):
        content = "[[Special:Filepath/Pauly-Wissowa_S_II,_0001.jpg|S II, 1]] : [http://www.archive.org/download/PWRE68/Pauly-Wissowa_S_II_0001.png IA]-158"
        result = self.re_importer._analyse_second_column(content)
        compare({"start": 1, "end": 158}, result)

    def test_second_column_wrong_content(self):
        content = "[[Special:Filepath/Pauly-Wissowa_S_II,_0001.jpg|bubu, 1]] : [http://www.archive.org/download/PWRE68/Pauly-Wissowa_S_II_0001.png IA]-158"
        with LogCapture():
            with self.assertRaises(AttributeError):
                result = self.re_importer._analyse_second_column(content)

    def test_second_column_same_column(self):
        content = "[[Special:Filepath/Pauly-Wissowa_S_II,_0001.jpg|S II, 1]] : [http://www.archive.org/download/PWRE68/Pauly-Wissowa_S_II_0001.png IA]"
        result = self.re_importer._analyse_second_column(content)
        compare({"start": 1, "end": 1}, result)

    def test_build_normal_line(self):
        line = """|[[RE:Herodes 14]]{{Anker|Herodes 14}}
|[[Special:Filepath/Pauly-Wissowa_S_II,_0001.jpg|S II, 1]] : [http://www.archive.org/download/PWRE68/Pauly-Wissowa_S_II_0001.png IA]-158
|Otto, Walter
|1941"""
        lemma = self.re_importer._build_lemma_from_line(line)
        expected_lemma = {"lemma": "Herodes 14", "next": "", "previous": "", "redirect": False,
                          "chapters": list()}
        expected_lemma["chapters"].append(dict({"author": "Otto, Walter", "start": 1, "end": 158}))
        compare(expected_lemma, lemma)

    def test_build_redirect_line(self):
        line = """|[[RE:Herodes 14]]{{Anker|Herodes 14}}
|[[Special:Filepath/Pauly-Wissowa_S_II,_0001.jpg|S II, 1]] : [http://www.archive.org/download/PWRE68/Pauly-Wissowa_S_II_0001.png IA]-158
|X
|1941"""
        lemma = self.re_importer._build_lemma_from_line(line)
        expected_lemma = {"lemma": "Herodes 14", "next": "", "previous": "", "redirect": True,
                          "chapters": list()}
        expected_lemma["chapters"].append(dict({"author": "", "start": 1, "end": 158}))
        compare(expected_lemma, lemma)

    def test_build_strange_line(self):
        line = """|[[RE:Herodes 14]]{{Anker|Herodes 14}}
|[[Special:Filepath/Pauly-Wissowa_S_II,_0001.jpg|S II, 1]] : [http://www.archive.org/download/PWRE68/Pauly-Wissowa_S_II_0001.png IA]-158
|?
|1941"""
        lemma = self.re_importer._build_lemma_from_line(line)
        expected_lemma = {"lemma": "Herodes 14", "next": "", "previous": "", "redirect": False,
                          "chapters": list()}
        expected_lemma["chapters"].append(dict({"author": "", "start": 1, "end": 158}))
        compare(expected_lemma, lemma)

    def test_build_register(self):
        text = """{|
|-
|[[RE:Herodes 14]]{{Anker|Herodes 14}}
|[[Special:Filepath/Pauly-Wissowa_S_II,_0001.jpg|S II, 1]] : [http://www.archive.org/download/PWRE68/Pauly-Wissowa_S_II_0001.png IA]-158
|Otto, Walter
|1941
|-
|[[RE:Herodes 15]]{{Anker|Herodes 15}}
|[[Special:Filepath/Pauly-Wissowa_S_II,_0157.jpg|S II, 158]] : [http://www.archive.org/download/PWRE68/Pauly-Wissowa_S_II_0157.png IA]-161
|Otto, Walter
|1941
|}
[[Kategorie:RE:Register|!]]
Zahl der Artikel: 15, davon [[:Kategorie:RE:Band S II|{{PAGESINCATEGORY:RE:Band S II|pages}} in Volltext]]."""
        register = self.re_importer._build_register(text)
        expectation = list()
        expected_lemma = {"lemma": "Herodes 14", "next": "", "previous": "", "redirect": False,
                          "chapters": list()}
        expected_lemma["chapters"].append(dict({"author": "Otto, Walter", "start": 1, "end": 158}))
        expectation.append(expected_lemma)
        expected_lemma = {"lemma": "Herodes 15", "next": "", "previous": "", "redirect": False,
                          "chapters": list()}
        expected_lemma["chapters"].append(dict({"author": "Otto, Walter", "start": 158, "end": 161}))
        expectation.append(expected_lemma)
        compare(expectation, register)

    def test_dump_register(self):
        lemma_text = """{|
|-
|[[RE:Herodes 14]]{{Anker|Herodes 14}}
|[[Special:Filepath/Pauly-Wissowa_S_II,_0001.jpg|S II, 1]] : [http://www.archive.org/download/PWRE68/Pauly-Wissowa_S_II_0001.png IA]-158
|Otto, Walter
|1941
|-
|[[RE:Herodes 15]]{{Anker|Herodes 15}}
|[[Special:Filepath/Pauly-Wissowa_S_II,_0157.jpg|S II, 158]] : [http://www.archive.org/download/PWRE68/Pauly-Wissowa_S_II_0157.png IA]-161
|Otto, Walter
|1941
|}
[[Kategorie:RE:Register|!]]
Zahl der Artikel: 15, davon [[:Kategorie:RE:Band S II|{{PAGESINCATEGORY:RE:Band S II|pages}} in Volltext]]."""
        self.re_importer._dump_register("I_1", lemma_text)
        expected = """- lemma: Herodes 14
  next: ''
  previous: ''
  redirect: false
  chapters:
  - start: 1
    end: 158
    author: Otto, Walter
- lemma: Herodes 15
  next: ''
  previous: ''
  redirect: false
  chapters:
  - start: 158
    end: 161
    author: Otto, Walter"""
        with open(Path(__file__).parent.joinpath("test_register").joinpath("I_1.yaml"), "r") as yaml_file:
            compare(expected, yaml_file.read())
