# pylint: disable=protected-access,no-self-use
from unittest.case import TestCase

from testfixtures import compare

from service.ws_re.register.author_crawler import AuthorCrawler


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

    def test_extract_author_infos(self):
        compare(("Klaus", "Alpers", ""), self.crawler._extract_author_infos("|Alpers, Klaus"))
        compare(("Franz", "Altheim", ""), self.crawler._extract_author_infos("Altheim, [Franz]"))
        compare(("Wolfgang", "Aly", "Wolfgang Aly"),
                self.crawler._extract_author_infos("|[[Wolfgang Aly|Aly, Wolf[gang]]]"))
        compare(("Walter", "Amelung", "Walter Amelung"),
                self.crawler._extract_author_infos("|'''[[Walter Amelung|Amelung, [Walter]]]'''"))
        compare(("Hermann", "Abert", "Hermann Abert"),
                self.crawler._extract_author_infos("|'''[[Hermann Abert|Abert, [Hermann]]]"))
        compare(("Martin", "Bang", ""), self.crawler._extract_author_infos("Bang, [Martin]{{Anker | B}}"))
        compare(("Johannes", "Zwicker", ""), self.crawler._extract_author_infos("Zwicker, Joh[annes = Hanns]"))
        compare(("Friedrich Walter", "Lenz", ""),
                self.crawler._extract_author_infos("Lenz, Friedrich [Walter] = (Levy, [Friedrich Walter])"))
        compare(("Eduard", "Thraemer", "Eduard Thraemer"),
                self.crawler._extract_author_infos("'''[[Eduard Thraemer|Thraemer [= Thrämer], Eduard]]'''"))
        compare(("", "Buren s. Van Buren", ""), self.crawler._extract_author_infos("Buren s. Van Buren"))
        compare(("Karl", "Praechter", ""), self.crawler._extract_author_infos("Praechter, K[arl]<nowiki></nowiki>"))
        compare(("Richard", "Wagner", "Richard Wagner (Philologe)"),
                self.crawler._extract_author_infos("'''[[Richard Wagner (Philologe)|Wagner, [Richard]]]'''"))
        compare(("Anton", "Baumstark", "Anton Baumstark junior"),
                self.crawler._extract_author_infos("'''[[Anton Baumstark junior|Baumstark, [Anton (jr.)]]]'''"))



    def test_extract_years(self):
        compare((1906, 1988), self.crawler._extract_years("1906–1988"))
        compare((1908, None), self.crawler._extract_years("1908–?"))
        compare((1933, None), self.crawler._extract_years("* 1933"))
        compare((1933, None), self.crawler._extract_years("data-sort-value=\"1932\" |* 1933"))
        compare((None, None), self.crawler._extract_years(""))

    # pylint: disable=line-too-long
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
|[[Karlhans Abel|Abel, Karlhans]]
|1919–1998
|X A, S XII, S XIV
|[[w:Karlhans Abel|Wikipedia]]
|-
|Abel, Walther
|1906–1987
|XVI,1
|[[w:Walther Abel|Wikipedia]]
|-
|Wolf [?]
|
|XXI,2–XXII,1
|<!-- siehe Diskussionsseite -->
|-
|Zwicker, Joh[annes = Hanns]
|1881–1969
|VII,2–IX,1, XI,1, XVI,1, XVII,2–XIX,1, XX,1–XXI,2, I A,2–III A,1, S V
|[[w:Johannes Zwicker|Wikipedia]]
|}

[[Kategorie:RE:Autoren|!]]"""

    def test_split_author_table(self):

        splitted_table = self.crawler._split_author_table(self.author_table)
        compare(5, len(splitted_table))
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

        expect = {"Kenneth Morgan Abbott": {"death": 1988, "birth": 1906, "first_name": "Kenneth Morgan", "last_name": "Abbott"}}
        compare(expect, self.crawler._get_author(author_sub_table.replace("##date##", "1906–1988")))

        expect = {"Kenneth Morgan Abbott": {"birth": 1906, "first_name": "Kenneth Morgan", "last_name": "Abbott"}}
        compare(expect, self.crawler._get_author(author_sub_table.replace("##date##", "1906")))

        expect = {"Kenneth Morgan Abbott": {"first_name": "Kenneth Morgan", "last_name": "Abbott"}}
        compare(expect, self.crawler._get_author(author_sub_table.replace("##date##", "")))

    def test_get_complete_authors(self):
        author_mapping = self.crawler.get_authors(self.author_table)
        expect = {"Kenneth Morgan Abbott": {"birth": 1906, "death": 1988, "first_name": "Kenneth Morgan", "last_name": "Abbott"},
                  "Karlhans Abel": {"birth": 1919, "death": 1998, "first_name": "Karlhans", "last_name": "Abel", "lemma": "Karlhans Abel"},
                  "Walther Abel": {"birth": 1906, "death": 1987, "first_name": "Walther", "last_name": "Abel"},
                  "Wolf ?": {"last_name": "Wolf ?"},
                  "Johannes Zwicker": {"birth": 1881, "death": 1969, "first_name": "Johannes", "last_name": "Zwicker"}}
        compare(expect, author_mapping)

    table_head = "{{|class=\"wikitable sortable\"\n|-\n!width=\"200\" | Name/Sigel\n!width=\"75\" " \
                 "| Lebenszeit\n!width=\"300\" | Mitarbeit\n!Personenartikel\n"
    table_bottom = "\n|}}\n\n[[Kategorie:RE:Autoren|!]]"

    def test_bug_kazarow(self):
        author = """|-
|Kazarow, Gabriel (Katsarov, Gavril I.)
|2222–3333
|
|"""
        author_table = self.table_head + author + self.table_bottom
        author_mapping = self.crawler.get_authors(author_table)
        expect = {"Gabriel Kazarow": {"birth": 2222, "death": 3333, "first_name": "Gabriel", "last_name": "Kazarow"}}
        compare(expect, author_mapping)

    def test_bug_groebe(self):
        author = """|-
|Groebe, P[aul]<!--Schreibung auch Gröbe-->
|2222–3333
|
|"""
        author_table = self.table_head + author + self.table_bottom
        author_mapping = self.crawler.get_authors(author_table)
        expect = {"Paul Groebe": {"birth": 2222, "death": 3333, "first_name": "Paul", "last_name": "Groebe"}}
        compare(expect, author_mapping)
