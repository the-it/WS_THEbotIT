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
        after = ARTICLE_TEMPLATE
        self.assertEqual(after, str(RePage(self.page_mock)))

    def test_back_to_str_combined(self):
        before = "{{REDaten}}\ntext\n{{REAutor|Autor.}}{{REDaten}}\ntext1\n{{REAutor|Autor1.}}"
        self.text_mock.return_value = before
        after = ARTICLE_TEMPLATE + "\n" \
                + ARTICLE_TEMPLATE.replace("text", "text1").replace("Autor.", "Autor1.")
        self.assertEqual(after, str(RePage(self.page_mock)))

    def test_back_to_str_combined_with_additional_text(self):
        before = "1{{REDaten}}\ntext\n{{REAutor|Autor.}}2{{REDaten}}\ntext1\n{{REAutor|Autor1.}}3"
        self.text_mock.return_value = before
        after = "1\n" + ARTICLE_TEMPLATE \
                + "\n2\n" + ARTICLE_TEMPLATE.replace("text", "text1").replace("Autor.", "Autor1.") \
                + "\n3"
        self.assertEqual(after, str(RePage(self.page_mock)))

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

    def test_delete(self):
        self.text_mock.return_value = ARTICLE_TEMPLATE \
                                      + ARTICLE_TEMPLATE.replace("text.", "tada.") \
                                      + ARTICLE_TEMPLATE
        re_page = RePage(self.page_mock)
        self.assertEqual(3, len(re_page))
        del re_page[1]
        self.assertEqual(2, len(re_page))
        self.assertFalse("tada" in str(re_page))

    def test_clean_article_list(self):
        self.text_mock.return_value = ARTICLE_TEMPLATE + "tada." + ARTICLE_TEMPLATE
        re_page = RePage(self.page_mock)
        self.assertEqual(3, len(re_page))
        re_page[1] = ""
        re_page.clean_articles()
        self.assertEqual(2, len(re_page))
        self.assertFalse("tada" in str(re_page))

    def test_hash(self):
        self.text_mock.return_value = ARTICLE_TEMPLATE
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
        self.text_mock.return_value = ARTICLE_TEMPLATE
        re_page = RePage(self.page_mock)
        compare("RE:Page", re_page.lemma)
        compare("Page", re_page.lemma_without_prefix)
        compare("[[RE:Page|Page]]", re_page.lemma_as_link)

    def test_has_changed(self):
        self.text_mock.return_value = "{{REDaten}}text{{REAutor|Autor.}}"
        re_page = RePage(self.page_mock)
        self.assertTrue(re_page.has_changed())

    def test_has_not_changed(self):
        self.text_mock.return_value = ARTICLE_TEMPLATE
        re_page = RePage(self.page_mock)
        self.assertFalse(re_page.has_changed())

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
        complex_article = """{{#lst:RE:Plinius 5/I}}
{{#lst:RE:Plinius 5/II}}
{{#lst:RE:Plinius 5/III}}
{{#lst:RE:Plinius 5/IV}}"""
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

    def test_filter_just_articles_from_article_list(self):
        self.text_mock.return_value = f"bla\n{ARTICLE_TEMPLATE}\nbla\n{ARTICLE_TEMPLATE}"
        re_page = RePage(self.page_mock)
        just_articles = re_page.only_articles
        compare(2, len(just_articles))
