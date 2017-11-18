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
