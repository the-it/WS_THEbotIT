from unittest import TestCase, mock

import pywikibot
from testfixtures import compare

from service.ws_re.template import ReDatenException, ARTICLE_TEMPLATE
from service.ws_re.template.article import Article
from service.ws_re.template.re_page import RePage


class TestRePage(TestCase):
    @mock.patch("service.ws_re.template.re_page.pywikibot.Page")
    @mock.patch("service.ws_re.template.re_page.pywikibot.Page.text",
                new_callable=mock.PropertyMock)
    # pylint: disable=arguments-differ
    def setUp(self, text_mock, page_mock):
        self.page_mock = page_mock
        self.text_mock = text_mock
        type(self.page_mock).text = self.text_mock

    def test_save_because_of_changes(self):
        before = "{{REDaten}}\ntext\n{{REAutor|Autor.}}"
        self.text_mock.return_value = before
        re_page = RePage(self.page_mock)
        re_page.save("reason")
        self.text_mock.assert_called_with(ARTICLE_TEMPLATE)
        self.page_mock.save.assert_called_once_with(summary="reason", botflag=True)

    def test_dont_save_because_no_changes(self):
        self.text_mock.return_value = ARTICLE_TEMPLATE
        re_page = RePage(self.page_mock)
        re_page.save("reason")
        self.assertFalse(self.page_mock.save.mock_calls)

    def test_append(self):
        self.text_mock.return_value = ARTICLE_TEMPLATE
        re_page = RePage(self.page_mock)
        self.assertEqual(1, len(re_page))
        article_text = "{{REAbschnitt}}\ntext\n{{REAutor|Some Author.}}"
        article = Article.from_text(article_text)
        re_page.append(article)
        self.assertEqual(2, len(re_page))
        with self.assertRaises(TypeError):
            re_page.append(1)

    def test_clean_article_list(self):
        self.text_mock.return_value = ARTICLE_TEMPLATE + "tada." + ARTICLE_TEMPLATE
        re_page = RePage(self.page_mock)
        self.assertEqual(3, len(re_page))
        re_page[1] = ""
        re_page.clean_articles()
        self.assertEqual(2, len(re_page))
        self.assertFalse("tada" in str(re_page))

    def test_page_is_locked(self):
        self.text_mock.return_value = ARTICLE_TEMPLATE

        def side_effect(summary, botflag):
            raise pywikibot.exceptions.LockedPage(self.page_mock)

        self.page_mock.save.side_effect = side_effect
        re_page = RePage(self.page_mock)
        re_page[0].text = "bla"
        with self.assertRaises(ReDatenException):
            re_page.save("reason")

    def test_page_is_locked_detect_it(self):
        self.text_mock.return_value = ARTICLE_TEMPLATE

        self.page_mock.protection.return_value = {"edit": ("sysop", "infinity"),
                                                  "move": ("sysop", "infinity")}
        re_page = RePage(self.page_mock)
        re_page[0].text = "bla"
        with self.assertRaises(ReDatenException):
            re_page.save("reason")

    def test_page_no_lock(self):
        self.text_mock.return_value = ARTICLE_TEMPLATE

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

    def test_get_splitted_article_list(self):
        before = """{{REDaten}}\ntext\n{{REAutor|Some Author.}}
{{REDaten}}\ntext\n{{REAutor|Some Author.}}text{{REAbschnitt}}\ntext\n{{REAutor|Some Author.}}
{{REDaten}}\ntext\n{{REAutor|Some Author.}}text{{REAbschnitt}}\ntext\n{{REAutor|Some Author.}}text"""
        self.text_mock.return_value = before
        re_page = RePage(self.page_mock)
        splitted_list = re_page.splitted_article_list
        compare(3, len(splitted_list))
        compare(1, len(splitted_list[0]))
        compare(3, len(splitted_list[1]))
        compare(4, len(splitted_list[2]))
        self.assertTrue(isinstance(splitted_list[1][1], str))
        self.assertTrue(isinstance(splitted_list[2][1], str))
        self.assertTrue(isinstance(splitted_list[2][3], str))

    def test_get_splitted_article_list_pre_text(self):
        before = """text{{REDaten}}\ntext\n{{REAutor|Some Author.}}text"""
        self.text_mock.return_value = before
        re_page = RePage(self.page_mock)
        splitted_list = re_page.splitted_article_list
        compare(2, len(splitted_list))
        compare(1, len(splitted_list[0]))
        compare(2, len(splitted_list[1]))
        self.assertTrue(isinstance(splitted_list[0][0], str))
        self.assertTrue(isinstance(splitted_list[1][1], str))

    def test_complex_page(self):
        complex_article = """{{REDaten}}\n{{#lst:RE:Plinius 5/I}}
{{#lst:RE:Plinius 5/II}}
{{#lst:RE:Plinius 5/III}}
{{#lst:RE:Plinius 5/IV}}
{{REAutor|Some Author.}}"""
        self.text_mock.return_value = complex_article
        re_page = RePage(self.page_mock)
        self.assertTrue(re_page.complex_construction)

    def test_add_error_cat(self):
        self.text_mock.return_value = ARTICLE_TEMPLATE
        re_page = RePage(self.page_mock)
        re_page.add_error_category("Name_of_Cat")
        compare(2, len(re_page))
        compare("[[Kategorie:Name_of_Cat]]", re_page[1])

    def test_add_error_cat_no_dublicate_category(self):
        self.text_mock.return_value = f"{ARTICLE_TEMPLATE}" \
                                      f"\n[[Kategorie:Name_of_Cat]]"
        re_page = RePage(self.page_mock)
        re_page.add_error_category("Name_of_Cat")
        compare(2, len(re_page))
        compare("[[Kategorie:Name_of_Cat]]", re_page[1])

    def test_add_error_cat_with_note(self):
        self.text_mock.return_value = ARTICLE_TEMPLATE
        re_page = RePage(self.page_mock)
        re_page.add_error_category("Name_of_Cat", "note")
        compare(2, len(re_page))
        compare("[[Kategorie:Name_of_Cat]]<!--note-->", re_page[1])

    def test_add_error_cat_with_already_there(self):
        self.text_mock.return_value = f"{ARTICLE_TEMPLATE}" \
                                      f"\n[[Kategorie:Name_of_Cat]]<!--note-->" \
                                      f"\n[[Kategorie:Other_Cat]]<!--other_error-->"
        re_page = RePage(self.page_mock)
        re_page.add_error_category("Name_of_Cat", "note")
        compare(2, len(re_page))
        compare("[[Kategorie:Name_of_Cat]]<!--note-->"
                "\n[[Kategorie:Other_Cat]]<!--other_error-->", re_page[1])

    def test_remove_error_cat(self):
        self.text_mock.return_value = f"{ARTICLE_TEMPLATE}" \
                                      f"\n[[Kategorie:Name_of_Cat]]<!--note-->"
        re_page = RePage(self.page_mock)
        re_page.remove_error_category("Name_of_Cat")
        compare(1, len(re_page))

    def test_remove_error_cat_other_cat_exists(self):
        self.text_mock.return_value = f"{ARTICLE_TEMPLATE}" \
                                      f"\n[[Kategorie:Name_of_Cat]]<!--note-->" \
                                      f"\n[[Kategorie:Other_Cat]]<!--note-->"
        re_page = RePage(self.page_mock)
        re_page.remove_error_category("Name_of_Cat")
        compare(2, len(re_page))
        compare("[[Kategorie:Other_Cat]]<!--note-->", re_page[1])

    def test_remove_error_cat_no_cat_there(self):
        self.text_mock.return_value = f"{ARTICLE_TEMPLATE}"
        re_page = RePage(self.page_mock)
        re_page.remove_error_category("Name_of_Cat")
        compare(1, len(re_page))
