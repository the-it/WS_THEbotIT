from collections.abc import Sequence

import pywikibot

from scripts.service.ws_re.data_types import RePage, ReArticle, ReProperty, ReDatenException
from test import *

article_template = """{{REDaten
|BAND=
|SPALTE_START=
|SPALTE_END=
|VORGÄNGER=
|NACHFOLGER=
|SORTIERUNG=
|KORREKTURSTAND=
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


class TestReProperty(TestCase):
    def test_init(self):
        re_property = ReProperty(name="Test", default=False)
        self.assertFalse(re_property.value)
        re_property.value = True
        self.assertTrue(re_property.value)
        with self.assertRaises(TypeError):
            re_property.value = "other"

    def test_format_bool(self):
        re_property = ReProperty(name="Test", default=False)
        self.assertEqual(str(re_property), "OFF")
        re_property.value = True
        self.assertEqual(str(re_property), "ON")

    def test_wrong_default(self):
        with self.assertRaises(TypeError):
            re_property = ReProperty(name="Test", default=1)
            str(re_property)

    def test_set_bool_with_ON_and_OFF(self):
        re_property = ReProperty(name="Test", default=False)
        re_property.value = "ON"
        self.assertTrue(re_property.value)
        re_property.value = "OFF"
        self.assertFalse(re_property.value)
        re_property.value = ""
        self.assertFalse(re_property.value)

    def test_hash(self):
        re_property = ReProperty(name="Test", default=False)
        pre_hash = hash(re_property)
        re_property.value = True
        self.assertNotEqual(pre_hash, hash(re_property))

        re_property = ReProperty(name="Test", default="")
        pre_hash = hash(re_property)
        re_property.value = "value"
        self.assertNotEqual(pre_hash, hash(re_property))


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

    def test_properties_exception(self):
        with self.assertRaises(ReDatenException):
            ReArticle(re_daten_properties={"BAND": 1})

    def test_simple_article(self):
        article_text = "{{REDaten}}text{{REAutor|Autor.}}"
        article = ReArticle.from_text(article_text)
        self.assertEqual("text", article.text)

    def test_simple_article_with_whitespaces(self):
        article_text = "{{REDaten}}\n\n\t   text\t   {{REAutor|Autor.}}"
        article = ReArticle.from_text(article_text)
        self.assertEqual("text", article.text)

    def test_from_text(self):
        article_text = "{{REDaten\n|BAND=III\n|SPALTE_START=1\n}}\ntext\n{{REAutor|Some Author.}}"
        article = ReArticle.from_text(article_text)
        self.assertEqual(article.author, "Some Author")
        self.assertEqual(article.text, "text")
        self.assertEqual(article.article_type, "REDaten")
        self.assertEqual(article["BAND"].value, "III")
        self.assertEqual(article["SPALTE_START"].value, "1")

    def test_from_text_wrong_keywords(self):
        article_text = "{{REDaten|WHATEVER=I}}" \
                       "\ntext\n{{REAutor|Some Author.}}"
        with self.assertRaisesRegex(ReDatenException,
                                    "REDaten has wrong key word. --> {.*?}"):
            ReArticle.from_text(article_text)

    def test_from_text_short_keywords(self):
        article_text = "{{REDaten|BD=I|SS=1|SE=2|VG=A|NF=B|SRT=TADA|KOR=fertig|WS=BLUB|WP=BLAB" \
                       "|XS={{START}}|XE={{END}}|GND=1234|SCH=OFF|TJ=1949|ÜB=ON|VW=OFF|NT=ON}}" \
                       "\ntext\n{{REAutor|Some Author.}}"
        article = ReArticle.from_text(article_text)
        self.assertEqual("I", article["BAND"].value)
        self.assertEqual("1", article["SPALTE_START"].value)
        self.assertEqual("2", article["SPALTE_END"].value)
        self.assertEqual("A", article["VORGÄNGER"].value)
        self.assertEqual("B", article["NACHFOLGER"].value)
        self.assertEqual("TADA", article["SORTIERUNG"].value)
        self.assertEqual("fertig", article["KORREKTURSTAND"].value)
        self.assertEqual("BLUB", article["WIKISOURCE"].value)
        self.assertEqual("BLAB", article["WIKIPEDIA"].value)
        self.assertEqual("{{START}}", article["EXTSCAN_START"].value)
        self.assertEqual("{{END}}", article["EXTSCAN_END"].value)
        self.assertEqual("1234", article["GND"].value)
        self.assertEqual("1949", article["TODESJAHR"].value)
        self.assertFalse(article["KEINE_SCHÖPFUNGSHÖHE"].value)
        self.assertTrue(article["ÜBERSCHRIFT"].value)
        self.assertFalse(article["VERWEIS"].value)
        self.assertTrue(article["NACHTRAG"].value)

    def test_from_text_wrong_property_in_REDaten(self):
        article_text = "{{REDaten\n|III\n|SPALTE_START=1\n}}\ntext\n{{REAutor|Some Author.}}"
        with self.assertRaisesRegex(ReDatenException,
                                    "REDaten has property without a key word. --> {.*?}"):
            ReArticle.from_text(article_text)

    def test_from_text_two_REDaten_templates(self):
        article_text = "{{REDaten}}{{REDaten}}\ntext\n{{REAutor|Some Author.}}"
        with self.assertRaisesRegex(ReDatenException, "Article has the wrong structure. "
                                                      "There must one start template"):
            ReArticle.from_text(article_text)

    def test_from_text_no_REDaten_templates(self):
        article_text = "\ntext\n{{REAutor|Some Author.}}"
        with self.assertRaisesRegex(ReDatenException, "Article has the wrong structure. "
                                                      "There must one start template"):
            ReArticle.from_text(article_text)

    def test_from_text_two_REAuthor_templates(self):
        article_text = "{{REDaten}}\ntext\n{{REAutor|Some Author.}}{{REAutor}}"
        with self.assertRaisesRegex(ReDatenException, "Article has the wrong structure. "
                                                      "There must one stop template"):
            ReArticle.from_text(article_text)

    def test_from_text_no_REAuthor_templates(self):
        article_text = "{{REDaten}}\ntext\n"
        with self.assertRaisesRegex(ReDatenException, "Article has the wrong structure. "
                                                      "There must one stop template"):
            ReArticle.from_text(article_text)

    def test_from_text_wrong_order_of_templates(self):
        article_text = "{{REAutor}}{{REDaten}}\ntext"
        with self.assertRaisesRegex(ReDatenException,
                                    "Article has the wrong structure. Wrong order of templates."):
            ReArticle.from_text(article_text)

    def test_complete_article(self):
        article_text = article_template
        ReArticle.from_text(article_text)

    def test_from_text_REAbschnitt(self):
        article_text = "{{REAbschnitt}}\ntext\n{{REAutor|Some Author.}}"
        article = ReArticle.from_text(article_text)
        self.assertEqual(article.article_type, "REAbschnitt")

    def test_from_text_text_in_front_of_article(self):
        article_text = "text{{REDaten}}text{{REAutor}}"
        with self.assertRaisesRegex(ReDatenException,
                                    "Article has the wrong structure. "
                                    "There is text in front of the article."):
            ReArticle.from_text(article_text)

    def test_from_text_text_after_article(self):
        article_text = "{{REDaten}}text{{REAutor}}text"
        with self.assertRaisesRegex(ReDatenException,
                                    "Article has the wrong structure. "
                                    "There is text after the article."):
            ReArticle.from_text(article_text)

    def test_to_text_simple(self):
        self.article.author = "Autor"
        self.article.text = "text"
        self.assertEqual(article_template, self.article.to_text())

    def test_to_text_REAbschnitt(self):
        text = """{{REAbschnitt}}
text
{{REAutor|Autor.}}"""
        self.article.author = "Autor"
        self.article.text = "text"
        self.article.article_type = "REAbschnitt"
        self.assertEqual(text, self.article.to_text())

    def test_to_text_changed_properties(self):
        text = article_template.replace("BAND=", "BAND=II")\
                               .replace("SPALTE_START=", "SPALTE_START=1000")\
                               .replace("WIKIPEDIA=", "WIKIPEDIA=Test")
        self.article.text = "text"
        self.article.author = "Autor"
        self.article["BAND"].value = "II"
        self.article["SPALTE_START"].value = "1000"
        self.article["WIKIPEDIA"].value = "Test"
        self.assertEqual(text, self.article.to_text())

    def test_hash(self):
        pre_hash = hash(self.article)
        self.article["BAND"].value = "II"
        self.assertNotEqual(pre_hash, hash(self.article))
        pre_hash = hash(self.article)
        self.article["SPALTE_START"].value = "1000"
        self.assertNotEqual(pre_hash, hash(self.article))


class TestRePage(TestCase):
    @mock.patch("scripts.service.ws_re.data_types.pywikibot.Page", autospec=pywikibot.Page)
    @mock.patch("scripts.service.ws_re.data_types.pywikibot.Page.text",
                new_callable=mock.PropertyMock)
    def setUp(self, text_mock, page_mock):
        self.page_mock = page_mock
        self.text_mock = text_mock
        type(self.page_mock).text = self.text_mock

    def test_is_list(self):
        self.assertTrue(issubclass(RePage, Sequence))

    def test_simple_RePage_with_one_article(self):
        test_text = "{{REDaten}}\ntext\n{{REAutor|Autor.}}"
        self.text_mock.return_value = test_text
        re_page = RePage(self.page_mock)
        self.assertEqual(1, len(re_page))
        re_article = re_page[0]
        self.assertTrue(isinstance(re_article, ReArticle))
        self.assertEqual("text", re_article.text)
        self.assertEqual("REDaten", re_article.article_type)
        self.assertEqual("Autor", re_article.author)

    def test_double_article(self):
        self.text_mock.return_value = "{{REDaten}}\ntext0\n{{REAutor|Autor0.}}\n{{REDaten}}\n" \
                                      "text1\n{{REAutor|Autor1.}}"
        re_page = RePage(self.page_mock)
        re_article_0 = re_page[0]
        re_article_1 = re_page[1]
        self.assertEqual("text0", re_article_0.text)
        self.assertEqual("text1", re_article_1.text)

    def test_combined_article_with_abschnitt(self):
        self.text_mock.return_value = "{{REDaten}}\ntext0\n{{REAutor|Autor0.}}" \
                                      "\n{{REAbschnitt}}\ntext1\n{{REAutor|Autor1.}}"
        re_page = RePage(self.page_mock)
        re_article_0 = re_page[0]
        re_article_1 = re_page[1]
        self.assertEqual("text0", re_article_0.text)
        self.assertEqual("text1", re_article_1.text)
        self.assertEqual("REAbschnitt", re_article_1.article_type)

    def test_combined_article_with_abschnitt_and_normal_article(self):
        self.text_mock.return_value = "{{REDaten}}\ntext0\n{{REAutor|Autor0.}}" \
                                      "\n{{REAbschnitt}}\ntext1\n{{REAutor|Autor1.}}" \
                                      "\n{{REDaten}}\ntext2\n{{REAutor|Autor2.}}"
        re_page = RePage(self.page_mock)
        re_article_0 = re_page[0]
        re_article_1 = re_page[1]
        re_article_2 = re_page[2]
        self.assertEqual("text0", re_article_0.text)
        self.assertEqual("text1", re_article_1.text)
        self.assertEqual("text2", re_article_2.text)

    def test_wrong_structure_too_much_REAutor(self):
        self.text_mock.return_value = "{{REDaten}}\ntext0\n{{REAutor|Autor0.}}" \
                                      "\ntext1\n{{REAutor|Autor1.}}"
        with self.assertRaises(ReDatenException):
            RePage(self.page_mock)

    def test_wrong_structure_order_of_templates_not_correct(self):
        self.text_mock.return_value = "{{REDaten}}\ntext0\n{{REDaten}}\n{{REAutor|Autor0.}}" \
                                      "\ntext1\n{{REAutor|Autor1.}}"
        with self.assertRaises(ReDatenException):
            RePage(self.page_mock)

    def test_back_to_str(self):
        before = "{{REDaten}}\ntext\n{{REAutor|Autor.}}"
        self.text_mock.return_value = before
        after = article_template
        self.assertEqual(after, str(RePage(self.page_mock)))

    def test_back_to_str_combined(self):
        before = "{{REDaten}}\ntext\n{{REAutor|Autor.}}{{REDaten}}\ntext1\n{{REAutor|Autor1.}}"
        self.text_mock.return_value = before
        after = article_template + "\n" \
                + article_template.replace("text", "text1").replace("Autor.", "Autor1.")
        self.assertEqual(after, str(RePage(self.page_mock)))

    def test_back_to_str_combined_with_additional_text(self):
        before = "1{{REDaten}}\ntext\n{{REAutor|Autor.}}2{{REDaten}}\ntext1\n{{REAutor|Autor1.}}3"
        self.text_mock.return_value = before
        after = "1\n" + article_template \
                + "\n2\n" + article_template.replace("text", "text1").replace("Autor.", "Autor1.") \
                + "\n3"
        self.assertEqual(after, str(RePage(self.page_mock)))

    def test_save_because_of_changes(self):
        before = "{{REDaten}}\ntext\n{{REAutor|Autor.}}"
        self.text_mock.return_value = before
        re_page = RePage(self.page_mock)
        re_page.save("reason")
        self.text_mock.assert_called_with(article_template)
        self.page_mock.save.assert_called_once_with(summary="reason", botflag=True)

    def test_dont_save_because_no_changes(self):
        self.text_mock.return_value = article_template
        re_page = RePage(self.page_mock)
        re_page.save("reason")
        self.assertFalse(self.page_mock.save.mock_calls)

    def test_append(self):
        self.text_mock.return_value = article_template
        re_page = RePage(self.page_mock)
        self.assertEqual(1, len(re_page))
        article_text = "{{REAbschnitt}}\ntext\n{{REAutor|Some Author.}}"
        article = ReArticle.from_text(article_text)
        re_page.append(article)
        self.assertEqual(2, len(re_page))
        with self.assertRaises(TypeError):
            re_page.append(1)

    def test_hash(self):
        self.text_mock.return_value = article_template
        re_page = RePage(self.page_mock)

        pre_hash = hash(re_page)
        re_page[0].text = "bada"
        self.assertNotEqual(pre_hash, hash(re_page))

        pre_hash = hash(re_page)
        re_page[0]["BAND"].value = "tada"
        self.assertNotEqual(pre_hash, hash(re_page))

        pre_hash = hash(re_page)
        article_text = "{{REAbschnitt}}\ntext\n{{REAutor|Some Author.}}"
        article = ReArticle.from_text(article_text)
        re_page.append(article)
        self.assertNotEqual(pre_hash, hash(re_page))

    def test_lemma(self):
        self.page_mock.title.return_value = "RE:Page"
        self.text_mock.return_value = article_template
        re_page = RePage(self.page_mock)
        self.assertEqual("RE:Page", re_page.lemma)

    def test_has_changed(self):
        self.text_mock.return_value = "{{REDaten}}text{{REAutor|Autor.}}"
        re_page = RePage(self.page_mock)
        self.assertTrue(re_page.has_changed())

    def test_has_not_changed(self):
        self.text_mock.return_value = article_template
        re_page = RePage(self.page_mock)
        self.assertFalse(re_page.has_changed())