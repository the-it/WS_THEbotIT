# pylint: disable=no-self-use,protected-access
from unittest import TestCase, mock

from service.ws_re.template.article import Article
from service.ws_re.template.re_page_complex import RePageComplex


class TestRePage(TestCase):
    @mock.patch("service.ws_re.template.re_page.pywikibot.Page")
    @mock.patch("service.ws_re.template.re_page.pywikibot.Page.text",
                new_callable=mock.PropertyMock)
    # pylint: disable=arguments-differ
    def setUp(self, text_mock, page_mock):
        self.page_mock: mock.Mock = page_mock
        self.text_mock: mock.PropertyMock = text_mock
        type(self.page_mock).text = self.text_mock

    def test_simple_RePage_with_one_article(self):
        test_text = ["{{REDaten}}\ntext\n{{REAutor|Autor.}}", "dsgdsf"]
        self.text_mock.side_effect = test_text
        re_page = RePageComplex(self.page_mock)
        self.assertEqual(1, len(re_page))
        re_article = re_page[0]
        self.assertTrue(isinstance(re_article, Article))
        self.assertEqual("text", re_article.text)
        self.assertEqual("REDaten", re_article.article_type)
        self.assertEqual(("Autor.", ""), re_article.author)
