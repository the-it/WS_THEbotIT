from collections.abc import Sequence
from unittest import TestCase
import unittest.mock as mock

from scripts.service.ws_re.data_types import RePage, ReArticle, ReProperty, ReDatenException


class TestReProperty(TestCase):
    def test_init(self):
        re_property = ReProperty(name="Test", default=False)
        self.assertFalse(re_property.value)
        re_property.value = True
        self.assertTrue(re_property.value)
        with self.assertRaises(TypeError):
            re_property.value = ""

    def test_format_bool(self):
        re_property = ReProperty(name="Test", default=False)
        self.assertEqual(str(re_property), "OFF")
        re_property.value = True
        self.assertEqual(str(re_property), "ON")

    def test_wrong_default(self):
        with self.assertRaises(TypeError):
            re_property = ReProperty(name="Test", default=1)
            str(re_property)


class TestReArticle(TestCase):
    def setUp(self):
        self.article = ReArticle()

    def test_article_type(self):
        self.assertEqual(self.article.article_type, "REDaten")
        self.article.article_type = "REAbschnitt"
        self.assertEqual(self.article.article_type, "REAbschnitt")
        article = ReArticle(article_type="REAbschnitt")
        self.assertEqual(article.article_type, "REAbschnitt")

    def test_wrong_article_type(self):
        with self.assertRaisesRegex(ReDatenException, "ReStuff is not a permitted article type."):
            ReArticle(article_type="ReStuff")

    def test_set_text(self):
        self.assertEqual(self.article.text, "")
        self.article.text = "bla"
        self.assertEqual(self.article.text, "bla")
        article = ReArticle(text="blub")
        self.assertEqual(article.text, "blub")

    def test_wrong_type_text(self):
        with self.assertRaisesRegex(ReDatenException, "Property text must be a string."):
            ReArticle(text=1)

    def test_set_author(self):
        self.assertEqual(self.article.author, "")
        self.article.author = "bla"
        self.assertEqual(self.article.author, "bla")
        article = ReArticle(author="blub")
        self.assertEqual(article.author, "blub")

    def test_wrong_type_author(self):
        with self.assertRaisesRegex(ReDatenException, "Property author must be a string."):
            ReArticle(author=1)

    def test_properties_access(self):
        self.assertFalse(self.article["NACHTRAG"].value)
        self.article["NACHTRAG"].value = True
        self.assertTrue(self.article["NACHTRAG"].value)
        with self.assertRaises(KeyError):
            self.article["SomeShit"].value = ""

    def test_properties_iterate(self):
        iterator = iter(self.article)
        self.assertEqual(next(iterator).name, "BAND")
        self.assertEqual(next(iterator).name, "SPALTE_START")
        self.assertEqual(next(iterator).name, "SPALTE_END")
        for i in range(5):
            next(iterator)
        self.assertEqual(next(iterator).name, "WIKISOURCE")
        for i in range(5):
            next(iterator)
        self.assertEqual(next(iterator).name, "ÜBERSCHRIFT")
        self.assertEqual(next(iterator).name, "VERWEIS")
        self.assertEqual(next(iterator).name, "NACHTRAG")
        self.assertEqual(len(self.article), 17)

    def test_properties_init(self):
        article = ReArticle(re_daten_properties={"BAND": "I 1", "NACHTRAG": True})
        self.assertEqual(str(article["BAND"]), "I 1")
        self.assertEqual(str(article["NACHTRAG"]), "ON")

    def test_from_text(self):
        article_text = "{{REDaten\n|BAND=III\n|SPALTE_START=1\n}}\ntext\n{{REAutor|Some Author.}}"
        article = ReArticle.from_text(article_text)
        self.assertEqual(article.author, "Some Author")
        self.assertEqual(article.text, "text")
        self.assertEqual(article.article_type, "REDaten")
        self.assertEqual(article["BAND"].value, "III")
        self.assertEqual(article["SPALTE_START"].value, "1")

    def test_from_text_wrong_property_in_REDaten(self):
        article_text = "{{REDaten\n|III\n|SPALTE_START=1\n}}\ntext\n{{REAutor|Some Author.}}"
        with self.assertRaisesRegex(ReDatenException,
                                    "REDaten has property without a key word. --> {.*?}"):
            article = ReArticle.from_text((article_text))

    def test_from_text_two_REDaten_templates(self):
        article_text = "{{REDaten}}{{REDaten}}\ntext\n{{REAutor|Some Author.}}"
        with self.assertRaisesRegex(ReDatenException,
                                    "Article has the wrong structure. There must one start template"):
            article = ReArticle.from_text((article_text))

    def test_from_text_no_REDaten_templates(self):
        article_text = "\ntext\n{{REAutor|Some Author.}}"
        with self.assertRaisesRegex(ReDatenException,
                                    "Article has the wrong structure. There must one start template"):
            article = ReArticle.from_text((article_text))

    def test_from_text_two_REAuthor_templates(self):
        article_text = "{{REDaten}}\ntext\n{{REAutor|Some Author.}}{{REAutor}}"
        with self.assertRaisesRegex(ReDatenException,
                                    "Article has the wrong structure. There must one stop template"):
            article = ReArticle.from_text((article_text))

    def test_from_text_no_REAuthor_templates(self):
        article_text = "{{REDaten}}\ntext\n"
        with self.assertRaisesRegex(ReDatenException,
                                    "Article has the wrong structure. There must one stop template"):
            article = ReArticle.from_text((article_text))

    def test_from_text_wrong_order_of_templates(self):
        article_text = "{{REAutor}}{{REDaten}}\ntext"
        with self.assertRaisesRegex(ReDatenException,
                                    "Article has the wrong structure. Wrong order of templates."):
            article = ReArticle.from_text((article_text))

    def test_from_text_REAbschnitt(self):
        article_text = "{{REAbschnitt}}\ntext\n{{REAutor|Some Author.}}"
        article = ReArticle.from_text(article_text)
        self.assertEqual(article.article_type, "REAbschnitt")

    article_template = """{{REDaten
|BAND=
|SPALTE_START=
|SPALTE_END=
|VORGÄNGER=
|NACHFOLGER=
|SORTIERUNG=
|KORREKTURSTATUS=
|WIKIPEDIA=
|WIKISOURCE=
|EXTSCAN_START=
|EXTSCAN_END=
|GND=
|KEINE_SCHÖPFUNGSHÖHE=OFF
|TODESJAHR=
|ÜBERSCHRIFT=OFF
|VERWEIS=OFF
|NACHTRAG=OFF
}}
text
{{REAutor|Autor.}}"""

    def test_to_text_simple(self):
        self.article.author = "Autor"
        self.article.text = "text"
        self.assertEqual(self.article_template, self.article.to_text())

    def test_to_text_REAbschnitt(self):
        text = """{{REAbschnitt}}
text
{{REAutor|Autor.}}"""
        self.article.author = "Autor"
        self.article.text = "text"
        self.article.article_type = "REAbschnitt"
        self.assertEqual(text, self.article.to_text())

    def test_to_text_changed_properties(self):
        text = self.article_template.replace("BAND=", "BAND=II")\
                                    .replace("SPALTE_START=", "SPALTE_START=1000")\
                                    .replace("WIKIPEDIA=", "WIKIPEDIA=Test")
        self.article.text = "text"
        self.article.author = "Autor"
        self.article["BAND"].value = "II"
        self.article["SPALTE_START"].value = "1000"
        self.article["WIKIPEDIA"].value = "Test"
        self.assertEqual(text, self.article.to_text())


class TestRePage(TestCase):
    def setUp(self):
        self.page_mock = mock.MagicMock()
        self.text_mock = mock.PropertyMock(return_value="{{REDaten}}{{REAutor}}")
        type(self.page_mock).text = self.text_mock

    def test_initialize(self):
        self.text_mock.return_value = "2"
        RePage(self.page_mock)

    def test_ist_list(self):
        self.assertTrue(issubclass(RePage, Sequence))
