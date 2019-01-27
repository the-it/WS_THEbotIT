import copy
from collections import OrderedDict
from datetime import datetime
import os
import shutil
from collections.abc import Sequence
from pathlib import Path
from unittest import TestCase, mock, skipUnless, skip

import pywikibot
from testfixtures import compare

from scripts.service.ws_re.data_types import RePage, Article, Property, ReDatenException, \
    Volume, VolumeType, Volumes, Lemma, Author, Authors, \
    LemmaChapter, VolumeRegister, _REGISTER_PATH, Registers, AlphabeticRegister
from tools import path_or_str, INTEGRATION_TEST

_TEST_REGISTER_PATH = Path(__file__).parent.joinpath("test_register")

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
|GEBURTSJAHR=
|NACHTRAG=OFF
|ÜBERSCHRIFT=OFF
|VERWEIS=OFF
}}
text
{{REAutor|Autor.}}"""

def copy_test_data(source: str, destination: str):
    base_path = Path(__file__).parent
    shutil.copy(str(base_path.joinpath("test_data_register").joinpath(source + ".json")),
                str(base_path.joinpath("test_register").joinpath(destination + ".json")))


def clear_test_path():
    _TEST_FOLDER_PATH = Path(__file__).parent.joinpath("test_register")
    try:
        shutil.rmtree(path_or_str(_TEST_FOLDER_PATH))
    except FileNotFoundError:
        pass
    finally:
        os.mkdir(path_or_str(_TEST_FOLDER_PATH))


class TestReProperty(TestCase):
    def test_init(self):
        re_property = Property(name="Test", default=False)
        self.assertFalse(re_property.value)
        re_property.value = True
        self.assertTrue(re_property.value)
        with self.assertRaises(TypeError):
            re_property.value = "other"

    def test_format_bool(self):
        re_property = Property(name="Test", default=False)
        self.assertEqual(re_property.value_to_string(), "OFF")
        re_property.value = True
        self.assertEqual(re_property.value_to_string(), "ON")

    def test_wrong_default(self):
        with self.assertRaises(TypeError):
            re_property = Property(name="Test", default=1)
            re_property.value_to_string()

    def test_set_bool_with_ON_and_OFF(self):
        re_property = Property(name="Test", default=False)
        re_property.value = "ON"
        self.assertTrue(re_property.value)
        re_property.value = "OFF"
        self.assertFalse(re_property.value)
        re_property.value = ""
        self.assertFalse(re_property.value)

    def test_set_bool_bug_non_capitalized(self):
        re_property = Property(name="Test", default=False)
        re_property.value = "on"
        self.assertTrue(re_property)

    def test_set_value_not_stripped(self):
        re_property = Property(name="Test", default=False)
        re_property.value = "ON         "
        self.assertTrue(re_property)
        re_property_text = Property(name="Text", default="")
        re_property_text.value = "foo              "
        compare("foo", re_property_text.value)

    def test_hash(self):
        re_property = Property(name="Test", default=False)
        pre_hash = hash(re_property)
        re_property.value = True
        self.assertNotEqual(pre_hash, hash(re_property))

        re_property = Property(name="Test", default="")
        pre_hash = hash(re_property)
        re_property.value = "value"
        self.assertNotEqual(pre_hash, hash(re_property))

    def test_repr(self):
        re_property = Property(name="Test", default=False)
        compare("<ReProperty> (name: Test, value: False, type: <class 'bool'>)", repr(re_property))


class TestReArticle(TestCase):
    def setUp(self):
        self.article = Article()

    def test_article_type(self):
        self.assertEqual(self.article.article_type, "REDaten")
        self.article.article_type = "REAbschnitt"
        self.assertEqual(self.article.article_type, "REAbschnitt")
        article = Article(article_type="REAbschnitt")
        self.assertEqual(article.article_type, "REAbschnitt")

    def test_wrong_article_type(self):
        with self.assertRaisesRegex(ReDatenException, "ReStuff is not a permitted article type."):
            Article(article_type="ReStuff")

    def test_set_text(self):
        self.assertEqual(self.article.text, "")
        self.article.text = "bla"
        self.assertEqual(self.article.text, "bla")
        article = Article(text="blub")
        self.assertEqual(article.text, "blub")

    def test_wrong_type_text(self):
        with self.assertRaisesRegex(ReDatenException, "Property text must be a string."):
            Article(text=1)

    def test_set_author(self):
        self.assertEqual(self.article.author, ("", ""))
        self.article.author = "bla"
        self.assertEqual(self.article.author, ("bla", ""))
        article = Article(author=("blub", "II,2"))
        self.assertEqual(article.author, ("blub", "II,2"))

    def test_wrong_type_author(self):
        with self.assertRaises(ReDatenException):
            Article(author=1)

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
        for i in range(6):
            next(iterator)
        self.assertEqual(next(iterator).name, "NACHTRAG")
        self.assertEqual(next(iterator).name, "ÜBERSCHRIFT")
        self.assertEqual(next(iterator).name, "VERWEIS")
        self.assertEqual(len(self.article), 18)

    def test_properties_init(self):
        article = Article(re_daten_properties={"BAND": "I 1", "NACHTRAG": True})
        self.assertEqual(article["BAND"].value_to_string(), "I 1")
        self.assertEqual(article["NACHTRAG"].value_to_string(), "ON")

    def test_properties_exception(self):
        with self.assertRaises(ReDatenException):
            Article(re_daten_properties={"BAND": 1})

    def test_simple_article(self):
        article_text = "{{REDaten}}text{{REAutor|Autor.}}"
        article = Article.from_text(article_text)
        self.assertEqual("text", article.text)

    def test_simple_article_with_whitespaces(self):
        article_text = "{{REDaten}}\n\n\t   text\t   {{REAutor|Autor.}}"
        article = Article.from_text(article_text)
        self.assertEqual("text", article.text)

    def test_from_text(self):
        article_text = "{{REDaten\n|BAND=III\n|SPALTE_START=1\n}}\ntext\n{{REAutor|Some Author.}}"
        article = Article.from_text(article_text)
        self.assertEqual(article.author, ("Some Author.", ""))
        self.assertEqual(article.text, "text")
        self.assertEqual(article.article_type, "REDaten")
        self.assertEqual(article["BAND"].value, "III")
        self.assertEqual(article["SPALTE_START"].value, "1")

    def test_from_text_wrong_keywords(self):
        article_text = "{{REDaten|WHATEVER=I}}" \
                       "\ntext\n{{REAutor|Some Author.}}"
        with self.assertRaisesRegex(ReDatenException,
                                    "REDaten has wrong key word. --> {.*?}"):
            Article.from_text(article_text)

    def test_from_text_short_keywords(self):
        article_text = "{{REDaten|BD=I|SS=1|SE=2|VG=A|NF=B|SRT=TADA|KOR=fertig|WS=BLUB|WP=BLAB" \
                       "|XS={{START}}|XE={{END}}|GND=1234|KSCH=OFF|TJ=1949|ÜB=ON|VW=OFF|NT=ON}}" \
                       "\ntext\n{{REAutor|Some Author.}}"
        article = Article.from_text(article_text)
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
            Article.from_text(article_text)

    def test_from_text_two_REDaten_templates(self):
        article_text = "{{REDaten}}{{REDaten}}\ntext\n{{REAutor|Some Author.}}"
        with self.assertRaisesRegex(ReDatenException, "Article has the wrong structure. "
                                                      "There must one start template"):
            Article.from_text(article_text)

    def test_from_text_no_REDaten_templates(self):
        article_text = "\ntext\n{{REAutor|Some Author.}}"
        with self.assertRaisesRegex(ReDatenException, "Article has the wrong structure. "
                                                      "There must one start template"):
            Article.from_text(article_text)

    def test_from_text_two_REAuthor_templates(self):
        article_text = "{{REDaten}}\ntext\n{{REAutor|Some Author.}}{{REAutor}}"
        with self.assertRaisesRegex(ReDatenException, "Article has the wrong structure. "
                                                      "There must one stop template"):
            Article.from_text(article_text)

    def test_from_text_no_REAuthor_templates(self):
        article_text = "{{REDaten}}\ntext\n"
        with self.assertRaisesRegex(ReDatenException, "Article has the wrong structure. "
                                                      "There must one stop template"):
            Article.from_text(article_text)

    def test_from_text_wrong_order_of_templates(self):
        article_text = "{{REAutor}}{{REDaten}}\ntext"
        with self.assertRaisesRegex(ReDatenException,
                                    "Article has the wrong structure. Wrong order of templates."):
            Article.from_text(article_text)

    def test_complete_article(self):
        article_text = article_template
        Article.from_text(article_text)

    def test_from_text_REAbschnitt(self):
        article_text = "{{REAbschnitt}}\ntext\n{{REAutor|Some Author.}}"
        article = Article.from_text(article_text)
        self.assertEqual(article.article_type, "REAbschnitt")

    def test_from_text_text_in_front_of_article(self):
        article_text = "text{{REDaten}}text{{REAutor}}"
        with self.assertRaisesRegex(ReDatenException,
                                    "Article has the wrong structure. "
                                    "There is text in front of the article."):
            Article.from_text(article_text)

    def test_from_text_text_after_article(self):
        article_text = "{{REDaten}}text{{REAutor}}text"
        with self.assertRaisesRegex(ReDatenException,
                                    "Article has the wrong structure. "
                                    "There is text after the article."):
            Article.from_text(article_text)

    def test_to_text_simple(self):
        self.article.author = "Autor."
        self.article.text = "text"
        self.assertEqual(article_template, self.article.to_text())

    def test_to_text_REAbschnitt(self):
        text = """{{REAbschnitt}}
text
{{REAutor|Autor.}}"""
        self.article.author = "Autor."
        self.article.text = "text"
        self.article.article_type = "REAbschnitt"
        self.assertEqual(text, self.article.to_text())

    def test_to_text_changed_properties(self):
        text = article_template.replace("BAND=", "BAND=II")\
                               .replace("SPALTE_START=", "SPALTE_START=1000")\
                               .replace("WIKIPEDIA=", "WIKIPEDIA=Test")
        self.article.text = "text"
        self.article.author = "Autor."
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

    def test_bug_1(self):
        test_string = """{{REDaten
|BAND=IV,1
|SPALTE_START=610
|SPALTE_END=OFF
|VORGÄNGER=Cominius 23
|NACHFOLGER=Cominius 25
|SORTIERUNG=
|KORREKTURSTAND=Platzhalter
|KSCH=OFF
|TJ=1950
|WIKIPEDIA=
|WIKISOURCE=
|EXTSCAN_START={{REIA|IV,1|607}}
|EXTSCAN_END=
|VW=
}} 
'''24)''' ''L. Cominius Vipsanius Salutaris, domo Roma, subproc(urator) ludi magni, proc(urator) alimentor(um) per Apuliam Calabriam Lucaniam Bruttios, proc. prov(inciae) Sicil(iae), proc. capiend(orum) vec(tigalium) (?), proc. prov. Baet(icae), a cognitionib(us) domini n(ostri) Imp(eratoris) etc. etc. <!-- L. Septimi Severi Pertinac(is) Augusti, p(erfectissimus) v(ir), optimus vir et integrissimus'', CIL II 1085 = [[Hermann Dessau|{{SperrSchrift|Dessau}}]] 1406 (Ilipa); die Ehrung durch einen Untergebenen in der Baetica erfolgte bei seinem Abgang aus der Provinz, als er zu den Cognitiones des Kaisers berufen wurde. Die ''Cominia L. fil. Vipsania Dignitas c(larissima)f(emina)'', CIL IX 2336, könnte seine Tochter sein. -->

{{REAutor|Stein.}}"""
        Article.from_text(test_string)

    def test_bug_2(self):
        test_string = """{{REDaten
|BAND=XIV,1
|SPALTE_START=46
|SPALTE_END=
|VORGÄNGER=Lysippe 7
|NACHFOLGER=Lysippos 2
|SORTIERUNG=
|KORREKTURSTAND=unkorrigiert
|KSCH=on
|TJ=1962
|WIKIPEDIA=
|WIKISOURCE=
|EXTSCAN_START={{REWL|XIV,1|45}}
|EXTSCAN_END=
|GND=
}}
'''Lysippos. 1)''' Spartaner, führt unter König Agis und als sein Nachfolger Truppen gegen Elis (400/399): Xen. hell. IH 2 29f.
{{REAutor|Kahrstedt.}}"""
        Article.from_text(test_string)

    def test_correct_case(self):
        article_text = "{{REDaten\n|Nachtrag=OFF|Ksch=OFF\n}}\ntext\n{{REAutor|Autor.}}"
        article = Article.from_text(article_text)
        self.assertEqual(article_template, article.to_text())

    def test_bug_dot_added_to_author(self):
        article_text = "{{REAbschnitt}}\ntext\n{{REAutor|S.A.†}}"
        article = Article.from_text(article_text)
        self.assertIn("{{REAutor|S.A.†}}", article.to_text())

    def test_bug_issue_number_deleted_from_author(self):
        article_text = "{{REAbschnitt}}\ntext\n{{REAutor|Some Author.|I,1}}"
        article = Article.from_text(article_text)
        compare("I,1", article.author[1])
        self.assertIn("{{REAutor|Some Author.|I,1}}", article.to_text())

    def test_bug_issue_OFF_deleted_from_author(self):
        article_text = "{{REAbschnitt}}\ntext\n{{REAutor|OFF}}"
        article = Article.from_text(article_text)
        self.assertIn("{{REAutor|OFF}}", article.to_text())

    def test_bug_issue_OFF_deleted_from_author_no_OFF(self):
        article_text = "{{REAbschnitt}}\ntext\n{{REAutor|A. Author.}}"
        article = Article.from_text(article_text)
        self.assertIn("{{REAutor|A. Author.}}", article.to_text())


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
        self.assertTrue(isinstance(re_article, Article))
        self.assertEqual("text", re_article.text)
        self.assertEqual("REDaten", re_article.article_type)
        self.assertEqual(("Autor.", ""), re_article.author)

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

    def test_wrong_structure_corrupt_template(self):
        self.text_mock.return_value = "{{REDaten}}\ntext0\n{{REAutor|Autor1."
        with self.assertRaises(ReDatenException):
            RePage(self.page_mock)
        self.text_mock.return_value = "{{REDaten\ntext0\n{{REAutor|Autor1.}}"
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
        article = Article.from_text(article_text)
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
        article = Article.from_text(article_text)
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

    def test_page_is_locked(self):
        self.text_mock.return_value = article_template

        def side_effect(summary, botflag):
            raise pywikibot.exceptions.LockedPage(self.page_mock)
        self.page_mock.save.side_effect = side_effect
        re_page = RePage(self.page_mock)
        re_page[0].text = "bla"
        with self.assertRaises(ReDatenException):
            re_page.save("reason")

    def test_page_is_locked_detect_it(self):
        self.text_mock.return_value = article_template

        self.page_mock.protection.return_value = {'edit': ('sysop', 'infinity'),
                                                  'move': ('sysop', 'infinity')}
        re_page = RePage(self.page_mock)
        re_page[0].text = "bla"
        with self.assertRaises(ReDatenException):
            re_page.save("reason")

    def test_page_no_lock(self):
        self.text_mock.return_value = article_template

        self.page_mock.protection.return_value = {}
        re_page = RePage(self.page_mock)
        re_page[0].text = "bla"
        re_page.save("reason")

    def test_bug_too_much_blanks(self):
        before = """{{REAbschnitt}}
text
{{REAutor|Oberhummer.}}
<u>Anmerkung WS:</u><br /><references/>"""
        self.text_mock.return_value = before
        after = """{{REAbschnitt}}
text
{{REAutor|Oberhummer.}}
<u>Anmerkung WS:</u><br /><references/>"""
        self.assertEqual(after, str(RePage(self.page_mock)))


class TestVolume(TestCase):
    def test_init(self):
        volume = Volume("I,1", "1900", "Aal", "Bethel")
        compare("I,1", volume.name)
        compare("I_1", volume.file_name)
        compare("1900", volume.year)
        compare("Aal", volume.start)
        compare("Bethel", volume.end)

    def test_init_by_name(self):
        volume = Volume(name="I,1", year="1900", start="Aal", end="Bethel")
        compare("I,1", volume.name)
        compare("I_1", volume.file_name)
        compare("1900", volume.year)
        compare("Aal", volume.start)
        compare("Bethel", volume.end)

    def test_init_supp_or_register(self):
        volume = Volume(name="S I", year="1900")
        compare("S I", volume.name)
        compare("1900", volume.year)
        self.assertIsNone(volume.start)
        self.assertIsNone(volume.end)

    def test_init_year_as_int(self):
        volume = Volume(name="S I", year=1900)
        compare("S I", volume.name)
        compare("1900", volume.year)

    def test_volume_type(self):
        volume = Volume("I,1", "1900", "Aal", "Bethel")
        compare(VolumeType.FIRST_SERIES, volume.type)
        volume = Volume("I A,1", "1900", "Aal", "Bethel")
        compare(VolumeType.SECOND_SERIES, volume.type)
        volume = Volume("S II", "1900", "Aal", "Bethel")
        compare(VolumeType.SUPPLEMENTS, volume.type)
        volume = Volume("R", "1900", "Aal", "Bethel")
        compare(VolumeType.REGISTER, volume.type)
        with self.assertRaises(ReDatenException):
            volume = Volume("R I", "1900", "Aal", "Bethel").type

    def test_sortkey(self):
        volume = Volume("I,1", "1900", "Aal", "Bethel")
        compare("1_01_1", volume.sortkey)
        volume = Volume("IX A,2", "1900", "Aal", "Bethel")
        compare("2_09_2", volume.sortkey)
        volume = Volume("X A", "1900", "Aal", "Bethel")
        compare("2_10_None", volume.sortkey)
        volume = Volume("S IV", "1900", "Aal", "Bethel")
        compare("3_04", volume.sortkey)
        volume = Volume("R", "1900", "Aal", "Bethel")
        compare("4", volume.sortkey)



class TestVolumes(TestCase):
    def setUp(self):
        self.re_volumes = Volumes()

    def test_len(self):
        self.assertEqual(84, len(self.re_volumes))

    def test_iter(self):
        iterator = iter(self.re_volumes)
        self.assertEqual("I,1", iterator.__next__())
        for i in range(0, 47):
            iterator.__next__()
        self.assertEqual("XXIV", iterator.__next__())
        self.assertEqual("I A,1", iterator.__next__())
        for i in range(0, 17):
            iterator.__next__()
        self.assertEqual("X A", iterator.__next__())
        self.assertEqual("S I", iterator.__next__())
        for i in range(0, 13):
            iterator.__next__()
        self.assertEqual("S XV", iterator.__next__())
        self.assertEqual("R", iterator.__next__())

    def test_iter_first_series(self):
        counter = 0
        for volume in self.re_volumes.first_series:
            compare(VolumeType.FIRST_SERIES, volume.type)
            counter += 1
        compare(49, counter)

    def test_iter_second_series(self):
        counter = 0
        for volume in self.re_volumes.second_series:
            compare(VolumeType.SECOND_SERIES, volume.type)
            counter += 1
        compare(19, counter)

    def test_iter_supplements(self):
        counter = 0
        for volume in self.re_volumes.supplements:
            compare(VolumeType.SUPPLEMENTS, volume.type)
            counter += 1
        compare(15, counter)

    def test_iter_register(self):
        counter = 0
        for volume in self.re_volumes.register:
            compare(VolumeType.REGISTER, volume.type)
            counter += 1
        compare(1, counter)

    def test_iter_all_volumes(self):
        counter = 0
        current_type = VolumeType.FIRST_SERIES
        following_types = [VolumeType.SECOND_SERIES,
                           VolumeType.SUPPLEMENTS,
                           VolumeType.REGISTER]
        for volume in self.re_volumes.all_volumes:
            compare(Volume, type(volume))
            if volume.type == current_type:
                pass
            elif volume.type == following_types[0]:
                current_type = following_types[0]
                del following_types[0]
            else:  # pragma: no cover
                raise TypeError("The types hasn't the right order. This section should never reached")
            counter += 1
        compare(84, counter)

    def test_get(self):
        with self.assertRaises(ReDatenException):
            test = self.re_volumes["tada"]
        with self.assertRaises(ReDatenException):
            test = self.re_volumes[1]
        compare("I,1", self.re_volumes["I,1"].name)


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
            with self.assertRaises(ReDatenException):
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
        with self.assertRaises(ReDatenException):
            re_register_lemma = Lemma(no_chapter_dict, self.volumes["I,1"], self.authors)
        no_chapter_dict = {"lemma": "lemma", "chapters": [{"start": 1}]}
        with self.assertRaises(ReDatenException):
            re_register_lemma = Lemma(no_chapter_dict, self.volumes["I,1"], self.authors)

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
        uvwij_dict = copy.deepcopy(self.basic_dict)
        uvwij_dict["lemma"] = "UvWij"
        uvwij_lemma = Lemma(uvwij_dict, self.volumes["I,1"], self.authors)
        compare("uuuii", uvwij_lemma.sortkey)


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
        b_register = AlphabeticRegister("be", None, self.registers)
        compare(5, len(a_register))
        compare(5, len(b_register))
        compare("Aal", a_register[0]["lemma"])
        compare("Baaba", a_register[4]["lemma"])
        compare("Beta", b_register[0]["lemma"])
        compare("Vaaa", b_register[4]["lemma"])
        compare("Ueee", b_register[5]["lemma"])

    def test_squash_lemmas(self):
        register = AlphabeticRegister(None, "Be", OrderedDict())
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
        register = AlphabeticRegister(None, "Be", OrderedDict())
        expection = []
        compare(expection, register.squash_lemmas([]))

    def test_make_table(self):
        b_register = AlphabeticRegister("be", None, self.registers)
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
        iterator = iter(registers)
        compare("I,1", next(iterator).volume.name)
        for i in range(83):
            last = next(iterator)
        compare("R", last.volume.name)
        compare(84, len(registers))
        compare("IV,1", registers["IV,1"].volume.name)

    def test_not_all_there(self):
        copy_test_data("I_1_base", "I_1")
        registers = Registers()

    def test_alphabetic(self):
        copy_test_data("I_1_alpha", "I_1")
        copy_test_data("III_1_alpha", "III_1")
        registers = Registers()
        compare(44, len(registers.alphabetic_registers))
        compare(4, len(registers.alphabetic_registers["a"]))
        compare(2, len(registers.alphabetic_registers["b"]))
        compare(1, len(registers.alphabetic_registers["ch"]))
        compare(1, len(registers.alphabetic_registers["da"]))
        compare(2, len(registers.alphabetic_registers["u"]))

