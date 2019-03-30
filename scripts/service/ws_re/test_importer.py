import os
import shutil
from collections import OrderedDict
from pathlib import Path
from unittest import TestCase

from testfixtures import compare, LogCapture

from scripts.service.ws_re.importer import ReImporter


class TestReImporter(TestCase):
    _TEST_FOLDER_PATH = Path(__file__).parent.joinpath("test_register")

    def _set_up_test_folder(self):
        try:
            shutil.rmtree(self._TEST_FOLDER_PATH)
        except FileNotFoundError:
            pass
        finally:
            os.mkdir(self._TEST_FOLDER_PATH)

    def setUp(self):
        self.re_importer = ReImporter(log_to_screen=False, log_to_wiki=False, debug=False)
        self._set_up_test_folder()
        self.re_importer._register_folder = "test_register"
        self.re_importer.folder = Path(__file__).parent.joinpath(self.re_importer._register_folder)

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
                self.re_importer._split_line(line)


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
                self.re_importer._analyse_second_column(content)

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
        expected_lemma = {"lemma": "Herodes 14", "next": "", "previous": "",
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
        expected_lemma["chapters"].append(dict({"start": 1, "end": 158}))
        compare(expected_lemma, lemma)

    def test_build_strange_line(self):
        line = """|[[RE:Herodes 14]]{{Anker|Herodes 14}}
|[[Special:Filepath/Pauly-Wissowa_S_II,_0001.jpg|S II, 1]] : [http://www.archive.org/download/PWRE68/Pauly-Wissowa_S_II_0001.png IA]-158
|?
|1941"""
        lemma = self.re_importer._build_lemma_from_line(line)
        expected_lemma = {"lemma": "Herodes 14", "next": "", "previous": "",
                          "chapters": list()}
        expected_lemma["chapters"].append(dict({"start": 1, "end": 158}))
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
        expected_lemma = {"lemma": "Herodes 14", "next": "", "previous": "",
                          "chapters": list()}
        expected_lemma["chapters"].append(dict({"author": "Otto, Walter", "start": 1, "end": 158}))
        expectation.append(expected_lemma)
        expected_lemma = {"lemma": "Herodes 15", "next": "", "previous": "",
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
        expected = """[
  {
    "lemma": "Herodes 14",
    "next": "Herodes 15",
    "chapters": [
      {
        "start": 1,
        "end": 158,
        "author": "Otto, Walter"
      }
    ]
  },
  {
    "lemma": "Herodes 15",
    "previous": "Herodes 14",
    "chapters": [
      {
        "start": 158,
        "end": 161,
        "author": "Otto, Walter"
      }
    ]
  }
]"""
        with open(self._TEST_FOLDER_PATH.joinpath("I_1.json"), "r") as json_file:
            compare(expected, json_file.read())

    def test_register_already_there(self):
        with open(self._TEST_FOLDER_PATH.joinpath("I_1.json"), "w") as json_file:
            json_file.write("test")
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
        with open(self._TEST_FOLDER_PATH.joinpath("I_1.json"), "r") as json_file:
            compare("test", json_file.read())

    def test_make_dir(self):
        with open(self._TEST_FOLDER_PATH.joinpath("I_1.json"), "w") as json_file:
            json_file.write("test")
        self.re_importer.timestamp._last_run = True
        with LogCapture():
            self.re_importer.clean_deprecated_register()
        with open(self._TEST_FOLDER_PATH.joinpath("I_1.json"), "r") as json_file:
            compare("test", json_file.read())
        self.re_importer.timestamp.last_run = None
        with LogCapture():
            self.re_importer.clean_deprecated_register()
        self.assertFalse(os.path.exists(self._TEST_FOLDER_PATH.joinpath("I_1.json")))
        self.assertTrue(os.path.exists(self._TEST_FOLDER_PATH))
        os.removedirs(self._TEST_FOLDER_PATH)
        with LogCapture():
            self.re_importer.clean_deprecated_register()
        self.assertTrue(os.path.exists(self._TEST_FOLDER_PATH))

    def test_optimize_register(self):
        lemma_text = """{|
|-
|[[RE:Aquilinus 5]]{{Anker|Aquilinus 5}}
|[[Special:Filepath/Pauly-Wissowa_II,1,_0321.jpg|II,1, 322]] : [http://www.archive.org/download/PWRE03-04/Pauly-Wissowa_II1_0321.png IA]
|Seeck
|1921
|-
|[[RE:Aquilinus 6]]{{Anker|Aquilinus 6}}
|[[Special:Filepath/Pauly-Wissowa_II,1,_0321.jpg|II,1, 322]] : [http://www.archive.org/download/PWRE03-04/Pauly-Wissowa_II1_0321.png IA]
|Freudenthal
|1907
|-
|[[RE:Aquilinus 6]]{{Anker|Aquilinus 6}}
|[[Special:Filepath/Pauly-Wissowa_II,1,_0321.jpg|II,1, 322]] : [http://www.archive.org/download/PWRE03-04/Pauly-Wissowa_II1_0321.png IA]
|Rohden
|1939
|-
|[[RE:Aquilinus 6]]{{Anker|Aquilinus 6}}
|[[Special:Filepath/Pauly-Wissowa_II,1,_0321.jpg|II,1, 322]] : [http://www.archive.org/download/PWRE03-04/Pauly-Wissowa_II1_0321.png IA]-324
|AHörnchen
|1939
|-
|[[RE:Aquilinus 6]]{{Anker|Aquilinus 6}}
|[[Special:Filepath/Pauly-Wissowa_II,1,_0321.jpg|II,1, 324]] : [http://www.archive.org/download/PWRE03-04/Pauly-Wissowa_II1_0321.png IA]-329
|BHörnchen
|1939
|-
|[[RE:Aquilius]]{{Anker|Aquilius}}
|[[Special:Filepath/Pauly-Wissowa_II,1,_0321.jpg|II,1, 322]] : [http://www.archive.org/download/PWRE03-04/Pauly-Wissowa_II1_0321.png IA]
|
|
|}
[[Kategorie:RE:Register|!]]
Zahl der Artikel: 15, davon [[:Kategorie:RE:Band S II|{{PAGESINCATEGORY:RE:Band S II|pages}} in Volltext]]."""
        register = self.re_importer._build_register(lemma_text)
        compare(6, len(register))
        register = self.re_importer._optimize_register(register)
        compare(3, len(register))
        compare(4, len(register[1]["chapters"]))
        compare(OrderedDict((("start", 322), ("end", 322), ("author", "Freudenthal"))), register[1]["chapters"][0])
        compare(OrderedDict((("start", 322), ("end", 322), ("author", "Rohden"))),register[1]["chapters"][1])
        compare(OrderedDict((("start", 322), ("end", 324), ("author", "AHörnchen"))), register[1]["chapters"][2])
        compare(OrderedDict((("start", 324), ("end", 329), ("author", "BHörnchen"))),register[1]["chapters"][3])

    def test_pre_post_register(self):
        lemma_text = """{|
|-
|[[RE:Aquilinus 5]]{{Anker|Aquilinus 5}}
|[[Special:Filepath/Pauly-Wissowa_II,1,_0321.jpg|II,1, 322]] : [http://www.archive.org/download/PWRE03-04/Pauly-Wissowa_II1_0321.png IA]
|Seeck
|1921
|-
|[[RE:Aquilinus 6]]{{Anker|Aquilinus 6}}
|[[Special:Filepath/Pauly-Wissowa_II,1,_0321.jpg|II,1, 322]] : [http://www.archive.org/download/PWRE03-04/Pauly-Wissowa_II1_0321.png IA]
|Freudenthal
|1907
|-
|[[RE:Aquilius]]{{Anker|Aquilius}}
|[[Special:Filepath/Pauly-Wissowa_II,1,_0321.jpg|II,1, 322]] : [http://www.archive.org/download/PWRE03-04/Pauly-Wissowa_II1_0321.png IA]
|
|
|}
[[Kategorie:RE:Register|!]]
Zahl der Artikel: 15, davon [[:Kategorie:RE:Band S II|{{PAGESINCATEGORY:RE:Band S II|pages}} in Volltext]]."""
        register = self.re_importer._build_register(lemma_text)
        compare("", register[0]["next"])
        compare("", register[0]["previous"])
        compare("", register[1]["next"])
        compare("", register[1]["previous"])
        compare("", register[2]["next"])
        compare("", register[2]["previous"])
        register = self.re_importer._add_pre_post_register(register)
        compare("Aquilinus 6", register[0]["next"])
        with self.assertRaises(KeyError):
            print(register[0]["previous"])
        compare("Aquilius", register[1]["next"])
        compare("Aquilinus 5", register[1]["previous"])
        with self.assertRaises(KeyError):
            print(register[2]["next"])
        compare("Aquilinus 6", register[2]["previous"])

    def test_register_authors(self):
        self.re_importer.current_volume = "I,1"
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
|-
|[[RE:Herodes 14]]{{Anker|Herodes 14}}
|[[Special:Filepath/Pauly-Wissowa_S_II,_0001.jpg|S II, 1]] : [http://www.archive.org/download/PWRE68/Pauly-Wissowa_S_II_0001.png IA]-158
|B, A
|1941
|-
|[[RE:Herodes 15]]{{Anker|Herodes 15}}
|[[Special:Filepath/Pauly-Wissowa_S_II,_0157.jpg|S II, 158]] : [http://www.archive.org/download/PWRE68/Pauly-Wissowa_S_II_0157.png IA]-161
|C, D
|
|}
[[Kategorie:RE:Register|!]]
Zahl der Artikel: 15, davon [[:Kategorie:RE:Band S II|{{PAGESINCATEGORY:RE:Band S II|pages}} in Volltext]]."""
        self.re_importer._dump_register("I_1", lemma_text)
        self.re_importer.current_volume = "II,1"
        lemma_text = """{|
|-
|[[RE:Herodes 14]]{{Anker|Herodes 14}}
|[[Special:Filepath/Pauly-Wissowa_S_II,_0001.jpg|S II, 1]] : [http://www.archive.org/download/PWRE68/Pauly-Wissowa_S_II_0001.png IA]-158
|Otto, Walter
|1940
|-
|[[RE:Herodes 15]]{{Anker|Herodes 15}}
|[[Special:Filepath/Pauly-Wissowa_S_II,_0157.jpg|S II, 158]] : [http://www.archive.org/download/PWRE68/Pauly-Wissowa_S_II_0157.png IA]-161
|Otto, Walter
|1940
|}
[[Kategorie:RE:Register|!]]
Zahl der Artikel: 15, davon [[:Kategorie:RE:Band S II|{{PAGESINCATEGORY:RE:Band S II|pages}} in Volltext]]."""
        self.re_importer._dump_register("II_1", lemma_text)
        compare({"Otto, Walter": {"I,1": "1941", "II,1": "1940"}, "B, A": {"I,1": "1941"}, "C, D": {"I,1": ""}}, self.re_importer.authors)
        self.re_importer.current_volume = "III,1"
        lemma_text = """{|
|-
|[[RE:Herodes 14]]{{Anker|Herodes 14}}
|[[Special:Filepath/Pauly-Wissowa_S_II,_0001.jpg|S II, 1]] : [http://www.archive.org/download/PWRE68/Pauly-Wissowa_S_II_0001.png IA]-158
|Otto, Walter
|1940
|-
|[[RE:Herodes 15]]{{Anker|Herodes 15}}
|[[Special:Filepath/Pauly-Wissowa_S_II,_0157.jpg|S II, 158]] : [http://www.archive.org/download/PWRE68/Pauly-Wissowa_S_II_0157.png IA]-161
|Otto, Walter
|1941
|}
[[Kategorie:RE:Register|!]]
Zahl der Artikel: 15, davon [[:Kategorie:RE:Band S II|{{PAGESINCATEGORY:RE:Band S II|pages}} in Volltext]]."""
        with LogCapture():
            with self.assertRaises(ValueError):
                self.re_importer._dump_register("III_1", lemma_text)

    def test_dump_authors(self):
        self.re_importer.authors = {"Otto, Walter": {"I,1": "1941", "II,1": "", "III,1": "1941", "IV,1": "1942"},
                                    "B, A": {"I,1": "1941"},
                                    "C, D": {"I,1": ""}}
        compare({"1941": {"I,1", "III,1"}, "": {"II,1"}, "1942": {"IV,1"}},
                self.re_importer._convert_author("Otto, Walter"))
        self.re_importer._dump_authors()
        expected = """{
  "B, A": "B, A",
  "C, D": "C, D",
  "Otto, Walter": {
    "*": "Otto, Walter",
    "II,1": "Otto, Walter_II,1",
    "IV,1": "Otto, Walter_IV,1"
  }
}"""
        with open(self._TEST_FOLDER_PATH.joinpath("authors_mapping.json"), "r") as json_file:
            compare(expected, json_file.read())

        expected = """{
  "B, A": {
    "death": 1941
  },
  "C, D": {},
  "Otto, Walter": {
    "death": 1941
  },
  "Otto, Walter_II,1": {},
  "Otto, Walter_IV,1": {
    "death": 1942
  }
}"""
        with open(self._TEST_FOLDER_PATH.joinpath("authors.json"), "r") as json_file:
            compare(expected, json_file.read())


