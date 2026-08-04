# pylint: disable=protected-access,no-self-use
from unittest import TestCase, mock

from service.ws_re.register.authors import Authors
from service.ws_re.register.importer import ReImporter
from service.ws_re.register.lemma import Lemma
from service.ws_re.register.registers import Registers
from service.ws_re.register.test_base import BaseTestRegister
from service.ws_re.template import ReDatenException
from service.ws_re.template.article import Article
from service.ws_re.template.re_page import RePage
from service.ws_re.volumes import Volumes
from tools.test import real_wiki_test


class TestReImporter(TestCase):
    @real_wiki_test
    def test_adjust_end_column(self):
        registers = Registers()
        register = registers["XVI,1"]
        for idx, article in enumerate(register):
            if article.lemma == "Molorchos":
                # start test
                pre_1 = """{{REDaten
|BAND=XVI,1
|SPALTE_START=13
|SPALTE_END=OFF
|VORGÄNGER=Molorchia
|NACHFOLGER=Μόλος 1
}}
'''Molorchos'''
[...]
{{REAutor|J. Pley.}}"""
                self.assertTrue("SPALTE_END=14" in ReImporter.adjust_end_column(pre_1, register, idx))
                pre_2 = """{{REDaten
|BAND=XVI,1
|SPALTE_START=12
|SPALTE_END=OFF
|VORGÄNGER=Molorchia
|NACHFOLGER=Μόλος 1
}}
'''Molorchos'''
[...]
{{REAutor|J. Pley.}}"""
                # not clear don't do shit
                self.assertTrue("SPALTE_END=OFF" in ReImporter.adjust_end_column(pre_2, register, idx))
                # index out of range
                self.assertTrue("SPALTE_END=OFF" in ReImporter.adjust_end_column(pre_2, register, 9999))
                pre_3 = """{{REDaten
|BAND=XVI,1
|SPALTE_START=nothing
|SPALTE_END=OFF
|VORGÄNGER=Molorchia
|NACHFOLGER=Μόλος 1
}}
'''Molorchos'''
[...]
{{REAutor|J. Pley.}}"""
                # can't determine start column
                self.assertTrue("SPALTE_END=OFF" in ReImporter.adjust_end_column(pre_3, register, idx))
                pre_4 = """{{REDaten
|BAND=XVI,1
|SPALTE_START=14
|SPALTE_END=OFF
|VORGÄNGER=Molorchia
|NACHFOLGER=Μόλος 1
}}
'''Molorchos'''
[...]
{{REAutor|J. Pley.}}"""
                # start on the same column like follow article
                self.assertTrue("SPALTE_END=OFF" in ReImporter.adjust_end_column(pre_4, register, idx))


class TestGetTextBackup(BaseTestRegister):
    def setUp(self):
        self.authors = Authors()
        self.volume = Volumes()["I,1"]

    def _make_lemma(self, lemma: str, previous: str | None = None, next_: str | None = None) -> Lemma:
        lemma_dict = {"lemma": lemma}
        if previous is not None:
            lemma_dict["previous"] = previous
        if next_ is not None:
            lemma_dict["next"] = next_
        return Lemma.from_dict(lemma_dict, self.volume, self.authors)

    def test_uses_article_neighbors_when_set(self):
        article = self._make_lemma("Main", previous="Pre", next_="Post")
        pre = self._make_lemma("OtherPre")
        post = self._make_lemma("OtherPost")
        result = ReImporter.get_text_backup("I,1", article, pre, post)
        self.assertIn("|VORGÄNGER=Pre", result)
        self.assertIn("|NACHFOLGER=Post", result)

    def test_falls_back_to_neighbor_lemma_titles(self):
        article = self._make_lemma("Main")
        pre = self._make_lemma("NeighborPre")
        post = self._make_lemma("NeighborPost")
        result = ReImporter.get_text_backup("I,1", article, pre, post)
        self.assertIn("|VORGÄNGER=NeighborPre", result)
        self.assertIn("|NACHFOLGER=NeighborPost", result)

    def test_empty_when_no_source_and_no_neighbors(self):
        article = self._make_lemma("Main")
        result = ReImporter.get_text_backup("I,1", article)
        self.assertIn("|VORGÄNGER=\n", result)
        self.assertIn("|NACHFOLGER=\n", result)

    def test_mixed_article_and_neighbor(self):
        article = self._make_lemma("Main", previous="Pre")
        post = self._make_lemma("NeighborPost")
        result = ReImporter.get_text_backup("I,1", article, None, post)
        self.assertIn("|VORGÄNGER=Pre", result)
        self.assertIn("|NACHFOLGER=NeighborPost", result)


def _article(band: str, short_text: str = "") -> str:
    return (
        f"{{{{REDaten\n|BAND={band}\n|KURZTEXT={short_text}\n|NACHTRAG=OFF\n|ÜBERSCHRIFT=OFF\n}}}}"
        f"\ntext {band}\n{{{{REAutor|Some Author.}}}}"
    )


class TestAddArticleToLemma(TestCase):
    @mock.patch("service.ws_re.template.re_page.pywikibot.Page")
    @mock.patch("service.ws_re.template.re_page.pywikibot.Page.text", new_callable=mock.PropertyMock)
    # pylint: disable=arguments-differ
    def setUp(self, text_mock, page_mock):
        self.page_mock = page_mock
        self.text_mock = text_mock
        type(self.page_mock).text = self.text_mock

    def _re_page(self, *parts: str) -> RePage:
        self.text_mock.return_value = "\n".join(parts)
        return RePage(self.page_mock)

    def test_position_before_later_issue(self):
        re_page = self._re_page(_article("I A,1"), _article("R"))
        self.assertEqual(1, ReImporter.get_insert_position(re_page, "S XIV"))

    def test_position_in_front_of_all_articles(self):
        re_page = self._re_page(_article("R"))
        self.assertEqual(0, ReImporter.get_insert_position(re_page, "I A,1"))

    def test_position_behind_all_articles(self):
        re_page = self._re_page(_article("I A,1"))
        self.assertEqual(1, ReImporter.get_insert_position(re_page, "S XIV"))

    def test_position_in_front_of_categories(self):
        re_page = self._re_page(_article("I A,1"), "[[Kategorie:RE:Stammdaten überprüfen]]")
        self.assertEqual(1, ReImporter.get_insert_position(re_page, "S XIV"))

    def test_position_behind_text_of_last_article(self):
        re_page = self._re_page(_article("I A,1"), "<references/>")
        self.assertEqual(2, ReImporter.get_insert_position(re_page, "S XIV"))

    def test_get_short_text(self):
        re_page = self._re_page(_article("I A,1", "a short text"), _article("R", "another short text"))
        self.assertEqual("a short text", ReImporter.get_short_text(re_page))

    def test_get_short_text_of_a_later_article(self):
        re_page = self._re_page(_article("I A,1"), _article("R", "another short text"))
        self.assertEqual("another short text", ReImporter.get_short_text(re_page))

    def test_get_short_text_no_short_text_present(self):
        re_page = self._re_page(_article("I A,1"), _article("R"))
        self.assertEqual("", ReImporter.get_short_text(re_page))

    def test_split_trailing_categories(self):
        re_page = self._re_page(
            _article("I A,1"), "<references/>\n\n[[Kategorie:RE:Stammdaten überprüfen]]\n[[Kategorie:Tada]]"
        )
        ReImporter.split_trailing_categories(re_page)
        self.assertEqual("<references/>", re_page[1])
        self.assertEqual("[[Kategorie:RE:Stammdaten überprüfen]]\n[[Kategorie:Tada]]", re_page[2])
        self.assertEqual(2, ReImporter.get_insert_position(re_page, "S XIV"))

    def test_split_trailing_categories_nothing_to_split(self):
        re_page = self._re_page(_article("I A,1"), "[[Kategorie:Tada]]")
        ReImporter.split_trailing_categories(re_page)
        self.assertEqual(2, len(re_page))
        re_page = self._re_page(_article("I A,1"), "<references/>")
        ReImporter.split_trailing_categories(re_page)
        self.assertEqual(2, len(re_page))
        re_page = self._re_page(_article("I A,1"))
        ReImporter.split_trailing_categories(re_page)
        self.assertEqual(1, len(re_page))

    def test_no_position_issue_already_there(self):
        re_page = self._re_page(_article("I A,1"), _article("S XIV"), _article("R"))
        self.assertIsNone(ReImporter.get_insert_position(re_page, "S XIV"))

    def test_unknown_issue_on_page(self):
        re_page = self._re_page(_article("Tada"))
        with self.assertRaises(ReDatenException):
            ReImporter.get_insert_position(re_page, "S XIV")

    def test_adjust_nachtrag(self):
        re_page = self._re_page(_article("I A,1"), _article("S XIV"), _article("R"))
        ReImporter.adjust_nachtrag(re_page)
        flags = [(article["NACHTRAG"].value, article["ÜBERSCHRIFT"].value) for article in re_page.only_articles]
        self.assertEqual([(False, False), (True, True), (True, False)], flags)

    def test_insert_article_in_page(self):
        re_page = self._re_page(_article("I A,1"), "[[Kategorie:RE:Stammdaten überprüfen]]")
        position = ReImporter.get_insert_position(re_page, "S XIV")
        re_page.insert(position, Article.from_text(_article("S XIV")))
        ReImporter.adjust_nachtrag(re_page)
        page_text = str(re_page)
        self.assertLess(page_text.index("BAND=I A,1"), page_text.index("BAND=S XIV"))
        self.assertLess(page_text.index("BAND=S XIV"), page_text.index("[[Kategorie:"))
