# pylint: disable=no-self-use,protected-access
from unittest import TestCase, mock

from testfixtures import compare

from service.ws_re.template import ReDatenException, ARTICLE_TEMPLATE
from service.ws_re.template.article import Article
from service.ws_re.template.re_page_abstract import RePageAbstract


class TestRePage(TestCase):
    def setUp(self):
        self.page_mock = mock.Mock()
        self.text_mock = mock.PropertyMock()
        type(self.page_mock).text = self.text_mock

    class RePageImplMock(RePageAbstract):
        @property
        def is_writable(self) -> bool:
            return False

    def test_simple_RePage_with_one_article(self):
        test_text = "{{REDaten}}\ntext\n{{REAutor|Autor.}}"
        self.text_mock.return_value = test_text
        re_page = self.RePageImplMock(self.page_mock)
        self.assertEqual(1, len(re_page))
        re_article = re_page[0]
        self.assertTrue(isinstance(re_article, Article))
        self.assertEqual("text", re_article.text)
        self.assertEqual("REDaten", re_article.article_type)
        self.assertEqual(("Autor.", ""), re_article.author)

    def test_double_article(self):
        self.text_mock.return_value = "{{REDaten}}\ntext0\n{{REAutor|Autor0.}}\n{{REDaten}}\n" \
                                      "text1\n{{REAutor|Autor1.}}"
        re_page = self.RePageImplMock(self.page_mock)
        re_article_0 = re_page[0]
        re_article_1 = re_page[1]
        self.assertEqual("text0", re_article_0.text)
        self.assertEqual("text1", re_article_1.text)

    def test_combined_article_with_abschnitt(self):
        self.text_mock.return_value = "{{REDaten}}\ntext0\n{{REAutor|Autor0.}}" \
                                      "\n{{REAbschnitt}}\ntext1\n{{REAutor|Autor1.}}"
        re_page = self.RePageImplMock(self.page_mock)
        re_article_0 = re_page[0]
        re_article_1 = re_page[1]
        self.assertEqual("text0", re_article_0.text)
        self.assertEqual("text1", re_article_1.text)
        self.assertEqual("REAbschnitt", re_article_1.article_type)

    def test_combined_article_with_abschnitt_and_normal_article(self):
        self.text_mock.return_value = "{{REDaten}}\ntext0\n{{REAutor|Autor0.}}" \
                                      "\n{{REAbschnitt}}\ntext1\n{{REAutor|Autor1.}}" \
                                      "\n{{REDaten}}\ntext2\n{{REAutor|Autor2.}}"
        re_page = self.RePageImplMock(self.page_mock)
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
            self.RePageImplMock(self.page_mock)

    def test_raise_at_redirect(self):
        self.text_mock.return_value = "#WEITERLEITUNG [[RE:Bla]]"
        with self.assertRaises(ReDatenException):
            self.RePageImplMock(self.page_mock)

    def test_wrong_structure_order_of_templates_not_correct(self):
        self.text_mock.return_value = "{{REDaten}}\ntext0\n{{REDaten}}\n{{REAutor|Autor0.}}" \
                                      "\ntext1\n{{REAutor|Autor1.}}"
        with self.assertRaises(ReDatenException):
            self.RePageImplMock(self.page_mock)

    def test_wrong_structure_corrupt_template(self):
        self.text_mock.return_value = "{{REDaten}}\ntext0\n{{REAutor|Autor1."
        with self.assertRaises(ReDatenException):
            self.RePageImplMock(self.page_mock)
        self.text_mock.return_value = "{{REDaten\ntext0\n{{REAutor|Autor1.}}"
        with self.assertRaises(ReDatenException):
            self.RePageImplMock(self.page_mock)

    def test_back_to_str(self):
        before = "{{REDaten}}\ntext\n{{REAutor|Autor.}}"
        self.text_mock.return_value = before
        after = ARTICLE_TEMPLATE
        self.assertEqual(after, str(self.RePageImplMock(self.page_mock)))

    def test_back_to_str_combined(self):
        before = "{{REDaten}}\ntext\n{{REAutor|Autor.}}{{REDaten}}\ntext1\n{{REAutor|Autor1.}}"
        self.text_mock.return_value = before
        after = ARTICLE_TEMPLATE + "\n" \
                + ARTICLE_TEMPLATE.replace("text", "text1").replace("Autor.", "Autor1.")
        self.assertEqual(after, str(self.RePageImplMock(self.page_mock)))

    def test_back_to_str_combined_with_additional_text(self):
        before = "1{{REDaten}}\ntext\n{{REAutor|Autor.}}2{{REDaten}}\ntext1\n{{REAutor|Autor1.}}3"
        self.text_mock.return_value = before
        after = "1\n" + ARTICLE_TEMPLATE \
                + "\n2\n" + ARTICLE_TEMPLATE.replace("text", "text1").replace("Autor.", "Autor1.") \
                + "\n3"
        self.assertEqual(after, str(self.RePageImplMock(self.page_mock)))

    def test_delete(self):
        self.text_mock.return_value = ARTICLE_TEMPLATE \
                                      + ARTICLE_TEMPLATE.replace("text.", "tada.") \
                                      + ARTICLE_TEMPLATE
        re_page = self.RePageImplMock(self.page_mock)
        self.assertEqual(3, len(re_page))
        del re_page[1]
        self.assertEqual(2, len(re_page))
        self.assertFalse("tada" in str(re_page))

    def test_hash(self):
        self.text_mock.return_value = ARTICLE_TEMPLATE
        re_page = self.RePageImplMock(self.page_mock)

        pre_hash = hash(re_page)
        re_page[0].text = "bada"
        self.assertNotEqual(pre_hash, hash(re_page))

        pre_hash = hash(re_page)
        re_page[0]["BAND"].value = "tada"
        self.assertNotEqual(pre_hash, hash(re_page))

        pre_hash = hash(re_page)
        article_text = "{{REAbschnitt}}\ntext\n{{REAutor|Some Author.}}"
        article = Article.from_text(article_text)
        re_page._article_list.append(article)
        self.assertNotEqual(pre_hash, hash(re_page))

    def test_lemma(self):
        self.page_mock.title.return_value = "RE:Page"
        self.text_mock.return_value = ARTICLE_TEMPLATE
        re_page = self.RePageImplMock(self.page_mock)
        compare("RE:Page", re_page.lemma)
        compare("Page", re_page.lemma_without_prefix)
        compare("[[RE:Page|Page]]", re_page.lemma_as_link)

    def test_has_changed(self):
        self.text_mock.return_value = "{{REDaten}}text{{REAutor|Autor.}}"
        re_page = self.RePageImplMock(self.page_mock)
        self.assertTrue(re_page.has_changed())

    def test_has_not_changed(self):
        self.text_mock.return_value = ARTICLE_TEMPLATE
        re_page = self.RePageImplMock(self.page_mock)
        self.assertFalse(re_page.has_changed())

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
        self.assertEqual(after, str(self.RePageImplMock(self.page_mock)))

    def test_get_splitted_article_list(self):
        before = """{{REDaten}}\ntext\n{{REAutor|Some Author.}}
{{REDaten}}\ntext\n{{REAutor|Some Author.}}text{{REAbschnitt}}\ntext\n{{REAutor|Some Author.}}
{{REDaten}}\ntext\n{{REAutor|Some Author.}}text{{REAbschnitt}}\ntext\n{{REAutor|Some Author.}}text"""
        self.text_mock.return_value = before
        re_page = self.RePageImplMock(self.page_mock)
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
        re_page = self.RePageImplMock(self.page_mock)
        splitted_list = re_page.splitted_article_list
        compare(2, len(splitted_list))
        compare(1, len(splitted_list[0]))
        compare(2, len(splitted_list[1]))
        self.assertTrue(isinstance(splitted_list[0][0], str))
        self.assertTrue(isinstance(splitted_list[1][1], str))

    def test_filter_just_articles_from_article_list(self):
        self.text_mock.return_value = f"bla\n{ARTICLE_TEMPLATE}\nbla\n{ARTICLE_TEMPLATE}"
        re_page = self.RePageImplMock(self.page_mock)
        just_articles = re_page.only_articles
        compare(2, len(just_articles))

    def test_first_article(self):
        self.text_mock.return_value = f"bla\n{{{{REDaten}}}}\ntext1\n{{{{REAutor|xyz.}}}}\nbla\n{ARTICLE_TEMPLATE}"
        re_page = self.RePageImplMock(self.page_mock)
        first_article = re_page.first_article
        compare("text1", first_article.text)

    def test_set_article(self):
        self.text_mock.return_value = f"bla\n{{{{REDaten}}}}\ntext1\n{{{{REAutor|xyz.}}}}\nbla\n{ARTICLE_TEMPLATE}"
        re_page = self.RePageImplMock(self.page_mock)
        article_text = "{{REAbschnitt}}\ntextneu\n{{REAutor|Some Author.}}"
        article = Article.from_text(article_text)
        re_page[1] = article
        compare("textneu", re_page[1].text)
