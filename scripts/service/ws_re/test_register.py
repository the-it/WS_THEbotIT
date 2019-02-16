import copy
import os
import shutil
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from unittest import TestCase, skipUnless

from testfixtures import compare

from scripts.service.ws_re.data_types import _REGISTER_PATH, Volumes
from scripts.service.ws_re.register import Author, Authors, VolumeRegister, LemmaChapter, Lemma, \
    AlphabeticRegister, Registers, AuthorCrawler, RegisterException
from tools import INTEGRATION_TEST, path_or_str


_TEST_REGISTER_PATH = Path(__file__).parent.joinpath("test_register")


def copy_test_data(source: str, destination: str):
    base_path = Path(__file__).parent
    shutil.copy(str(base_path.joinpath("test_data_register").joinpath(source + ".json")),
                str(base_path.joinpath("test_register").joinpath(destination + ".json")))


def clear_test_path(renew_path=True):
    _TEST_FOLDER_PATH = Path(__file__).parent.joinpath("test_register")
    try:
        shutil.rmtree(path_or_str(_TEST_FOLDER_PATH))
    except FileNotFoundError:
        pass
    finally:
        if renew_path:
            os.mkdir(path_or_str(_TEST_FOLDER_PATH))


class TestAuthor(TestCase):
    def test_author(self):
        register_author = Author("Test Name", {"death": 1999})
        compare("Test Name", register_author.name)
        compare(1999, register_author.death)
        compare(None, register_author.birth)

        register_author = Author("Test Name", {"birth": 1999})
        compare(None, register_author.death)
        compare(1999, register_author.birth)


class BaseTestRegister(TestCase):
    @classmethod
    def setUpClass(cls):
        clear_test_path()
        copy_test_data("authors", "authors")
        copy_test_data("authors_mapping", "authors_mapping")
        Authors._REGISTER_PATH = _TEST_REGISTER_PATH
        VolumeRegister._REGISTER_PATH = _TEST_REGISTER_PATH

    @classmethod
    def tearDownClass(cls):
        Authors._REGISTER_PATH = _REGISTER_PATH
        VolumeRegister._REGISTER_PATH = _REGISTER_PATH
        clear_test_path(renew_path=False)


class TestAuthors(BaseTestRegister):
    def test_load_data(self):
        authors = Authors()
        author = authors.get_author_by_mapping("Abbott", "I,1")
        compare("Abbott", author.name)
        compare(None, author.death)
        author = authors.get_author_by_mapping("Abel", "I,1")
        compare("Abel", author.name)
        compare(1998, author.death)
        author = authors.get_author_by_mapping("Abel", "XVI,1")
        compare("Abel", author.name)
        compare(1987, author.death)
        compare(None, authors.get_author_by_mapping("Tada", "XVI,1"))

    def test_set_mapping(self):
        authors = Authors()
        compare("Abbott", authors._mapping["Abbott"])
        self.assertFalse("New" in authors._mapping)
        authors.set_mappings({"Abbott": "Abbott_new", "New": "New"})
        compare("Abbott_new", authors._mapping["Abbott"])
        compare("New", authors._mapping["New"])

    def test_set_author(self):
        authors = Authors()

        author = authors.get_author_by_mapping("Abel", "I,1")
        compare("Abel", author.name)
        compare(1998, author.death)
        compare(None, author.birth)
        authors.set_author({"Abel": {"birth": 1900, "death": 1990}})
        author = authors.get_author_by_mapping("Abel", "I,1")
        compare("Abel", author.name)
        compare(1990, author.death)
        compare(1900, author.birth)

        authors.set_author({"Abel2": {"birth": 1950}})
        author = authors._authors["Abel2"]
        compare("Abel2", author.name)
        compare(1950, author.birth)


class TestAuthorCrawler(TestCase):
    def setUp(self):
        self.crawler = AuthorCrawler()

    def test_split_mappings(self):
        test_str = """return {
["Karlhans Abel."] = "Karlhans Abel",

["Aly."] = "Wolfgang Aly",
["Wolf Aly."] = "Wolfgang Aly",

["Wünsch."] = {
	"Richard Wünsch",
	["R"] = "Albert Wünsch"
},

["Wolf."] = {
	["IX,2"] = "Karl Wolf",
	"? Wolf"
},

["Schwabe."] = {
	"Ernst Schwabe",
	["II,1"] = "Ludwig Schwabe",
	["IV,1"] = "Ludwig Schwabe",
	["VI,2"] = "Ludwig Schwabe"
},

["Zwicker."] = "Johannes Zwicker"
}
"""
        splitted_mapping = self.crawler._split_mappings(test_str)
        compare("[\"Karlhans Abel.\"] = \"Karlhans Abel\"", splitted_mapping[0])
        compare(7, len(splitted_mapping))
        expect = """["Wünsch."] = {
	"Richard Wünsch",
	["R"] = "Albert Wünsch"
}"""
        compare(expect, splitted_mapping[3])
        expect = """["Wolf."] = {
	["IX,2"] = "Karl Wolf",
	"? Wolf"
}"""
        compare(expect, splitted_mapping[4])
        expect = """["Schwabe."] = {
	"Ernst Schwabe",
	["II,1"] = "Ludwig Schwabe",
	["IV,1"] = "Ludwig Schwabe",
	["VI,2"] = "Ludwig Schwabe"
}"""
        compare(expect, splitted_mapping[5])

    def test_extract_mapping(self):
        expect = {"K A.": "Karlhans Abel"}
        compare(expect, self.crawler._extract_mapping("[\"K A.\"]     = 	\"Karlhans Abel\""))

        mapping_text = """["Schwabe."] = {
	"Ernst Schwabe",
	["II,1"] = "Ludwig Schwabe",
	["IV,1"] = "Ludwig Schwabe",
	["VI,2"] = "Ludwig Schwabe"
}"""
        expect = {"Schwabe.": {"*": "Ernst Schwabe",
                               "II,1": "Ludwig Schwabe",
                               "IV,1": "Ludwig Schwabe",
                               "VI,2": "Ludwig Schwabe"}}
        compare(expect, self.crawler._extract_mapping(mapping_text))

        mapping_text = """["Wolf."] = {
	["IX,2"] = "Karl Wolf",
	"? Wolf"
}"""
        expect = {"Wolf.": {"*": "? Wolf",
                            "IX,2": "Karl Wolf"}}
        compare(expect, self.crawler._extract_mapping(mapping_text))

        mapping_text = """["Wünsch."] = {
	"Richard Wünsch",
	["R"] = "Albert Wünsch"
}"""
        expect = {"Wünsch.": {"*": "Richard Wünsch",
                            "R": "Albert Wünsch"}}
        compare(expect, self.crawler._extract_mapping(mapping_text))

    def test_get_mapping(self):
        test_str = """return {
["Karlhans Abel."] = "Karlhans Abel",

["Wünsch."] = {
	"Richard Wünsch",
	["R"] = "Albert Wünsch"
},

["Zwicker."] = "Johannes Zwicker"
}
"""
        expect = {"Karlhans Abel.": "Karlhans Abel",
                  "Wünsch.": {"*": "Richard Wünsch",
                              "R": "Albert Wünsch"},
                  "Zwicker.": "Johannes Zwicker"}
        compare(expect, self.crawler.get_mapping(test_str))

    def test_extract_author_name(self):
        compare(("Klaus", "Alpers"), self.crawler._extract_author_name("|Alpers, Klaus"))
        compare(("Franz", "Altheim"), self.crawler._extract_author_name("Altheim, [Franz]"))
        compare(("Wolfgang", "Aly"), self.crawler._extract_author_name("|[[Wolfgang Aly|Aly, Wolf[gang]]]"))
        compare(("Walter", "Amelung"), self.crawler._extract_author_name("|'''[[Walter Amelung|Amelung, [Walter]]]'''"))
        compare(("Hermann", "Abert"), self.crawler._extract_author_name("|'''[[Hermann Abert|Abert, [Hermann]]]"))
        compare(("Martin", "Bang"), self.crawler._extract_author_name("Bang, [Martin]{{Anker | B}}"))
        compare(("Johannes", "Zwicker"), self.crawler._extract_author_name("Zwicker, Joh[annes = Hanns]"))
        compare(("Friedrich Walter", "Lenz"), self.crawler._extract_author_name("Lenz, Friedrich [Walter] = (Levy, [Friedrich Walter])"))
        compare(("Eduard", "Thraemer"), self.crawler._extract_author_name("'''[[Eduard Thraemer|Thraemer [= Thrämer], Eduard]]'''"))

    def test_extract_years(self):
        compare((1906, 1988), self.crawler._extract_years("1906–1988"))
        compare((1908, None), self.crawler._extract_years("1908–?"))
        compare((1933, None), self.crawler._extract_years("* 1933"))
        compare((1933, None), self.crawler._extract_years("data-sort-value=\"1932\" |* 1933"))
        compare((None, None), self.crawler._extract_years(""))

    author_table = """Das '''Autorenverzeichnis''' für ''[[Paulys Realencyclopädie der classischen Altertumswissenschaft]]'' basiert auf dem ''Verzeichnis der Autoren'' im Registerband 1980 (S. 235–250), enthält aber anders als dieses biografische Angaben und Verweise zu ggf. existierenden Wikipedia-Artikeln. Die Autoren, deren Werke gemeinfrei sind, werden '''fett''' hervorgehoben.

Die Redaktion der RE fügte ihrem Registerband ein Verzeichnis mit 1096 Autorennamen an (die 119 Autoren des ersten Bandes sind hervorgehoben), das von Gerhard Winkler erstellt wurde. Die Identifizierungen sind teilweise falsch, darum ist weitere Recherche empfohlen. Darüber hinaus tauchen manche Autoren, die nachweislich Beiträge erstellt haben, gar nicht auf. Auch in den Vorreden werden Personen als Beiträger genannt, die in Winklers Verzeichnis fehlen. Ob diese Personen tatsächlich Artikel verfasst oder der Redaktion nur Hinweise gegeben haben, bleibt zu untersuchen.

Als Kontrollgrundlage dienen in erster Linie die Angaben im Werk selbst:
*[[RE:Vorwort (Band I)|Vorwort zu Band I]] (Stand: 1894, 119 Mitarbeiter)
*[[RE:Mitarbeiter-Verzeichnis (Band II)|Mitarbeiter-Verzeichnis in Band II]] (Stand: 1896, 149 Mitarbeiter)
*[[RE:Vorwort (Supplementband I)|Vorwort zu Supplement-Heft I]] (Stand: 1903, 27 Namen freiwilliger Beiträger, nicht alle waren Artikelverfasser)
*[[RE:Verzeichnis der Mitarbeiter nach dem Stand vom 1. Mai 1913|Verzeichnis der Mitarbeiter nach dem Stand vom 1. Mai 1913]] (209 Mitarbeiter)
*Verlagsprospekt (Stand: 1931, 242 Mitarbeiter) {{IA|reverlagsprospekt1933}}
*[[:Datei:Pauly-Wissowa VII A,2,2 X02.jpg|Viten der Mitarbeiter]] (Stand: 1948, 27 Mitarbeiter mit Geburtsdaten)

{{TOC}}


{|class="wikitable sortable" 
|-
!width="200" | Name/Sigel
!width="75" | Lebenszeit
!width="300" | Mitarbeit
!Personenartikel
|-
|Abbott, K[enneth] M[organ]{{Anker|A}}
|1906–1988
|XIX,2
|[[w:Kenneth Morgan Abbott|Wikipedia]]
|-
|Abel, Karlhans
|1919–1998
|X A, S XII, S XIV
|[[w:Karlhans Abel|Wikipedia]]
|-
|Abel, Walther
|1906–1987
|XVI,1
|[[w:Walther Abel|Wikipedia]]
|-
|Zwicker, Joh[annes = Hanns]
|1881–1969
|VII,2–IX,1, XI,1, XVI,1, XVII,2–XIX,1, XX,1–XXI,2, I A,2–III A,1, S V
|[[w:Johannes Zwicker|Wikipedia]]
|}

[[Kategorie:RE:Autoren|!]]"""

    def test_split_author_table(self):

        splitted_table = self.crawler._split_author_table(self.author_table)
        compare(4, len(splitted_table))
        expected_entry = """|Abbott, K[enneth] M[organ]{{Anker|A}}
|1906–1988
|XIX,2
|[[w:Kenneth Morgan Abbott|Wikipedia]]"""
        compare(expected_entry, splitted_table[0])

    def test_split_author(self):
        author_sub_table = """|Abbott, K[enneth] M[organ]{{Anker|A}}
|1906–1988
|XIX,2
|[[w:Kenneth Morgan Abbott|Wikipedia]]"""
        splitted_author = self.crawler._split_author(author_sub_table)
        compare(4, len(splitted_author))
        compare("|Abbott, K[enneth] M[organ]{{Anker|A}}", splitted_author[0])
        compare("1906–1988", splitted_author[1])
        compare("XIX,2", splitted_author[2])
        compare("[[w:Kenneth Morgan Abbott|Wikipedia]]", splitted_author[3])

    def test_get_author_mapping(self):
        author_sub_table = """|Abbott, K[enneth] M[organ]{{Anker|A}}
|##date##
|XIX,2
|[[w:Kenneth Morgan Abbott|Wikipedia]]"""

        expect = {"Kenneth Morgan Abbott": {"death": 1988, "birth": 1906}}
        compare(expect, self.crawler._get_author(author_sub_table.replace("##date##", "1906–1988")))

        expect = {"Kenneth Morgan Abbott": {"birth": 1906}}
        compare(expect, self.crawler._get_author(author_sub_table.replace("##date##", "1906")))

        expect = {"Kenneth Morgan Abbott": {}}
        compare(expect, self.crawler._get_author(author_sub_table.replace("##date##", "")))

    def test_get_complete_authors(self):
        author_mapping = self.crawler.get_authors(self.author_table)
        expect = {"Kenneth Morgan Abbott": {"birth": 1906, "death": 1988},
                  "Karlhans Abel": {"birth": 1919, "death": 1998},
                  "Walther Abel": {"birth": 1906, "death": 1987},
                  "Johannes Zwicker": {"birth": 1881, "death": 1969}}
        compare(expect, author_mapping)


class TestLemmaChapter(TestCase):
    def test_error_in_is_valid(self):
        lemma_chapter = LemmaChapter(1)
        compare(False, lemma_chapter.is_valid())

    def test_no_author(self):
        lemma_chapter = LemmaChapter({"start": 1, "end": 2})
        compare(None, lemma_chapter.author)


class TestLemma(BaseTestRegister):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        self.authors = Authors()
        self.volumes = Volumes()

    def test_from_dict_errors(self):
        basic_dict = {"lemma": "lemma", "previous": "previous", "next": "next",
                      "redirect": True, "chapters": [{"start": 1, "end": 1, "author": "Abel"},
                                                     {"start": 1, "end": 2, "author": "Abbott"}]}

        for entry in ["lemma", "chapters"]:
            test_dict = copy.deepcopy(basic_dict)
            del test_dict[entry]
            with self.assertRaises(RegisterException):
                Lemma(test_dict, Volumes()["I,1"], self.authors)

        for entry in ["previous", "next", "redirect"]:
            test_dict = copy.deepcopy(basic_dict)
            del test_dict[entry]
            self.assertIsNone(Lemma(test_dict, Volumes()["I,1"], self.authors)[entry])

        re_register_lemma = Lemma(basic_dict, Volumes()["I,1"], self.authors)
        compare("lemma", re_register_lemma["lemma"])
        compare("previous", re_register_lemma["previous"])
        compare("next", re_register_lemma["next"])
        compare(True, re_register_lemma["redirect"])
        compare([{"start": 1, "end": 1, "author": "Abel"},
                 {"start": 1, "end": 2, "author": "Abbott"}],
                re_register_lemma["chapters"])
        compare(5, len(re_register_lemma))

    basic_dict = {"lemma": "lemma", "previous": "previous", "next": "next",
                  "redirect": True, "chapters": [{"start": 1, "end": 1, "author": "Abel"},
                                                 {"start": 1, "end": 2, "author": "Abbott"}]}

    def test_get_link(self):
        re_register_lemma = Lemma(self.basic_dict, self.volumes["I,1"], self.authors)
        compare("[[RE:lemma|{{Anker2|lemma}}]]", re_register_lemma.get_link())

    def test_get_pages(self):
        re_register_lemma = Lemma(self.basic_dict, self.volumes["I,1"], self.authors)
        compare("[[Special:Filepath/Pauly-Wissowa_I,1,_0001.jpg|1]]",
                re_register_lemma._get_pages(LemmaChapter({"start": 1, "end": 1, "author": "Abel"})))
        compare("[[Special:Filepath/Pauly-Wissowa_I,1,_0017.jpg|18]]",
                re_register_lemma._get_pages(LemmaChapter({"start": 18, "end": 18, "author": "Abel"})))
        compare("[[Special:Filepath/Pauly-Wissowa_I,1,_0197.jpg|198]]-200",
                re_register_lemma._get_pages(LemmaChapter({"start": 198, "end": 200, "author": "Abel"})))

    def test_get_author_and_year(self):
        re_register_lemma = Lemma(self.basic_dict, self.volumes["I,1"], self.authors)
        compare("Abert", re_register_lemma._get_author_str(
            LemmaChapter({"start": 1, "end": 2, "author": "Abert"})))
        compare("1927", re_register_lemma._get_death_year(
            LemmaChapter({"start": 1, "end": 2, "author": "Abert"})))
        compare("", re_register_lemma._get_death_year(
            LemmaChapter({"start": 1, "end": 2, "author": "Abbott"})))

        # check if author not there
        compare("????", re_register_lemma._get_death_year(
            LemmaChapter({"start": 1, "end": 2, "author": "Tada"})))
        compare("Tada", re_register_lemma._get_author_str(
            LemmaChapter({"start": 1, "end": 2, "author": "Tada"})))

        compare("", re_register_lemma._get_death_year(
            LemmaChapter({"start": 1, "end": 2})))
        compare("", re_register_lemma._get_author_str(
            LemmaChapter({"start": 1, "end": 2})))

    def test_year_format(self):
        year_free_content = datetime.now().year - 71
        compare("style=\"background:#B9FFC5\"", Lemma._get_year_format(str(year_free_content)))
        compare("style=\"background:#FFCBCB\"", Lemma._get_year_format(str(year_free_content + 1)))
        compare("style=\"background:#CBCBCB\"", Lemma._get_year_format(""))
        compare("style=\"background:#FFCBCB\"", Lemma._get_year_format("????"))
        compare("style=\"background:#FFCBCB\"", Lemma._get_year_format(None))

    def test_is_valid(self):
        no_chapter_dict = {"lemma": "lemma", "chapters": []}
        with self.assertRaises(RegisterException):
            print(Lemma(no_chapter_dict, self.volumes["I,1"], self.authors))
        no_chapter_dict = {"lemma": "lemma", "chapters": [{"start": 1}]}
        with self.assertRaises(RegisterException):
            print(Lemma(no_chapter_dict, self.volumes["I,1"], self.authors))

    def test_get_row(self):
        one_line_dict = {"lemma": "lemma", "previous": "previous", "next": "next",
                         "redirect": False, "chapters": [{"start": 1, "end": 1, "author": "Abel"}]}
        re_register_lemma = Lemma(one_line_dict, self.volumes["I,1"], self.authors)
        expected_row = """|-
|[[RE:lemma|{{Anker2|lemma}}]]
|[[Special:Filepath/Pauly-Wissowa_I,1,_0001.jpg|1]]
|Abel
|style="background:#FFCBCB"|1998"""
        compare(expected_row, re_register_lemma.get_table_row())
        two_line_dict = {"lemma": "lemma", "previous": "previous", "next": "next",
                         "redirect": False, "chapters": [{"start": 1, "end": 1, "author": "Abel"},
                                                         {"start": 1, "end": 4, "author": "Abbott"}]}
        re_register_lemma = Lemma(two_line_dict, self.volumes["I,1"], self.authors)
        expected_row = """|-
|rowspan=2|[[RE:lemma|{{Anker2|lemma}}]]
|[[Special:Filepath/Pauly-Wissowa_I,1,_0001.jpg|1]]
|Abel
|style="background:#FFCBCB"|1998
|-
|[[Special:Filepath/Pauly-Wissowa_I,1,_0001.jpg|1]]-4
|Abbott
|style="background:#CBCBCB"|"""
        compare(expected_row, re_register_lemma.get_table_row())
        expected_row = expected_row.replace("[[RE:lemma|{{Anker2|lemma}}]]", "I,1")
        compare(expected_row, re_register_lemma.get_table_row(print_volume=True))

    def test_sort_key(self):
        sort_dict = copy.deepcopy(self.basic_dict)
        "ßâçèéêëîïôöûüśūʾʿ"
        sort_dict["lemma"] = "Uv(Wij)'ï?ßçëäöüêśôʾʿâçèéêëîïôöûüśū"
        sort_lemma = Lemma(sort_dict, self.volumes["I,1"], self.authors)
        compare("uuuiiissceaouesoaceeeeiioouusu", sort_lemma.sort_key)

        sort_dict["lemma"] = "ad Flexum"
        uvwij_lemma = Lemma(sort_dict, self.volumes["I,1"], self.authors)
        compare("flexum", uvwij_lemma.sort_key)

        sort_dict["lemma"] = "ab epistulis"
        uvwij_lemma = Lemma(sort_dict, self.volumes["I,1"], self.authors)
        compare("epistulis", uvwij_lemma.sort_key)

        sort_dict["lemma"] = "a memoria"
        uvwij_lemma = Lemma(sort_dict, self.volumes["I,1"], self.authors)
        compare("memoria", uvwij_lemma.sort_key)

        sort_dict["lemma"] = "aabaa abfl"
        uvwij_lemma = Lemma(sort_dict, self.volumes["I,1"], self.authors)
        compare("aabaa abfl", uvwij_lemma.sort_key)

        sort_dict["lemma"] = "aabab abfl"
        uvwij_lemma = Lemma(sort_dict, self.volumes["I,1"], self.authors)
        compare("aabab abfl", uvwij_lemma.sort_key)

        sort_dict["lemma"] = "aabad abfl"
        uvwij_lemma = Lemma(sort_dict, self.volumes["I,1"], self.authors)
        compare("aabad abfl", uvwij_lemma.sort_key)

        sort_dict["lemma"] = "G. abfl"
        uvwij_lemma = Lemma(sort_dict, self.volumes["I,1"], self.authors)
        compare("abfl", uvwij_lemma.sort_key)

        sort_dict["lemma"] = "Abdigildus (?)"
        uvwij_lemma = Lemma(sort_dict, self.volumes["I,1"], self.authors)
        compare("abdigildus", uvwij_lemma.sort_key)

        sort_dict["lemma"] = "Abd 1 11 230"
        uvwij_lemma = Lemma(sort_dict, self.volumes["I,1"], self.authors)
        compare("abd 001 011 230", uvwij_lemma.sort_key)

        sort_dict["lemma"] = "E....orceni"
        uvwij_lemma = Lemma(sort_dict, self.volumes["I,1"], self.authors)
        compare("e    orceni", uvwij_lemma.sort_key)


class TestRegister(BaseTestRegister):
    def test_init(self):
        copy_test_data("I_1_base", "I_1")
        VolumeRegister(Volumes()["I,1"], Authors())

    def test_get_table(self):
        copy_test_data("I_1_two_entries", "I_1")
        register = VolumeRegister(Volumes()["I,1"], Authors())
        expected_table = """{|class="wikitable sortable"
!Artikel
!Seite
!Autor
!Sterbejahr
|-
|[[RE:Aal|{{Anker2|Aal}}]]
|[[Special:Filepath/Pauly-Wissowa_I,1,_0001.jpg|1]]-4
|Abel
|style="background:#FFCBCB"|1998
|-
|[[RE:Aarassos|{{Anker2|Aarassos}}]]
|[[Special:Filepath/Pauly-Wissowa_I,1,_0003.jpg|4]]
|Abert
|style="background:#B9FFC5"|1927
|}
[[Kategorie:RE:Register|!]]
Zahl der Artikel: 2, davon [[:Kategorie:RE:Band I,1|{{PAGESINCATEGORY:RE:Band I,1|pages}} in Volltext]]."""
        compare(expected_table, register.get_register_str())


class TestAlphabeticRegister(BaseTestRegister):
    def setUp(self):
        copy_test_data("I_1_alpha", "I_1")
        copy_test_data("III_1_alpha", "III_1")
        self.authors = Authors()
        self.volumes = Volumes()
        self.registers = OrderedDict()
        self.registers["I,1"] = VolumeRegister(self.volumes["I,1"], self.authors)
        self.registers["III,1"] = VolumeRegister(self.volumes["III,1"], self.authors)

    def test_init(self):
        a_register = AlphabeticRegister("a", "be", self.registers)
        b_register = AlphabeticRegister("be", "zzzzzz", self.registers)
        compare(5, len(a_register))
        compare(5, len(b_register))
        compare("Aal", a_register[0]["lemma"])
        compare("Baaba", a_register[4]["lemma"])
        compare("Beta", b_register[0]["lemma"])
        compare("Vaaa", b_register[4]["lemma"])
        compare("Ueee", b_register[5]["lemma"])

    def test_squash_lemmas(self):
        register = AlphabeticRegister("a", "be", OrderedDict())
        lemma1 = Lemma({"lemma": "lemma", "chapters": [{"start": 1, "end": 1, "author": "Abel"}]},
                        Volumes()["I,1"],
                        self.authors)
        lemma2 = Lemma({"lemma": "lemma", "chapters": [{"start": 1, "end": 1, "author": "Abel"}]},
                        Volumes()["III,1"],
                        self.authors)
        lemma3 = Lemma({"lemma": "lemma2", "chapters": [{"start": 1, "end": 1, "author": "Abel"}]},
                        Volumes()["III,1"],
                        self.authors)
        lemmas = [lemma1, lemma2, lemma3]
        expection = [[lemma1, lemma2], [lemma3]]
        compare(expection, register.squash_lemmas(lemmas))

    def test_squash_lemmas_empty(self):
        register = AlphabeticRegister("a", "be", OrderedDict())
        expection = []
        compare(expection, register.squash_lemmas([]))

    def test_make_table(self):
        b_register = AlphabeticRegister("be", "zzzzzz", self.registers)
        expected_table = """{|class="wikitable sortable"
!Artikel
!Band
!Seite
!Autor
!Sterbejahr
|-
|rowspan=3|[[RE:Beta|{{Anker2|Beta}}]]
|rowspan=2|I,1
|[[Special:Filepath/Pauly-Wissowa_I,1,_0003.jpg|4]]
|Abert
|style="background:#B9FFC5"|1927
|-
|[[Special:Filepath/Pauly-Wissowa_I,1,_0003.jpg|4]]-5
|Abel
|style="background:#FFCBCB"|1998
|-
|III,1
|[[Special:Filepath/Pauly-Wissowa_III,1,_0003.jpg|4]]
|Abbott
|style="background:#CBCBCB"|
|-
|[[RE:Charlie|{{Anker2|Charlie}}]]
|III,1
|[[Special:Filepath/Pauly-Wissowa_III,1,_0003.jpg|4]]
|Abel
|style="background:#FFCBCB"|1998
|-
|[[RE:Delta|{{Anker2|Delta}}]]
|III,1
|[[Special:Filepath/Pauly-Wissowa_III,1,_0003.jpg|4]]
|Abert
|style="background:#B9FFC5"|1927
|-
|[[RE:Vaaa|{{Anker2|Vaaa}}]]
|III,1
|[[Special:Filepath/Pauly-Wissowa_III,1,_0003.jpg|4]]
|Abert
|style="background:#B9FFC5"|1927
|-
|[[RE:Ueee|{{Anker2|Ueee}}]]
|III,1
|[[Special:Filepath/Pauly-Wissowa_III,1,_0003.jpg|4]]
|Abert
|style="background:#B9FFC5"|1927
|}
[[Kategorie:RE:Register|!]]
Zahl der Artikel: 6, """
        compare(expected_table, b_register.get_register_str())


class TestRegisters(BaseTestRegister):
    def test_init(self):
        for volume in Volumes().all_volumes:
            copy_test_data("I_1_base", volume.file_name)
        registers = Registers()
        iterator = iter(registers.volumes.values())
        compare("I,1", next(iterator).volume.name)
        for i in range(83):
            last = next(iterator)
        compare("R", last.volume.name)
        compare(84, len(registers.volumes))
        compare("IV,1", registers["IV,1"].volume.name)

    def test_not_all_there(self):
        copy_test_data("I_1_base", "I_1")
        Registers()

    def test_alphabetic(self):
        copy_test_data("I_1_alpha", "I_1")
        copy_test_data("III_1_alpha", "III_1")
        registers = Registers()
        compare(44, len(registers.alphabetic))
        compare(4, len(registers.alphabetic["a"]))
        compare(2, len(registers.alphabetic["b"]))
        compare(1, len(registers.alphabetic["ch"]))
        compare(1, len(registers.alphabetic["da"]))
        compare(2, len(registers.alphabetic["u"]))


_MAX_SIZE_WIKI_PAGE = 2098175


@skipUnless(INTEGRATION_TEST, "only execute in integration test")
class TestIntegrationRegister(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registers = Registers()

    def test_length_of_alphabetic(self):
        for register in self.registers.alphabetic.values():
            self.assertGreater(_MAX_SIZE_WIKI_PAGE, len(register.get_register_str()))