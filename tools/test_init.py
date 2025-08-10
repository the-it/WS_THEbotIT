# pylint: disable=protected-access, no-self-use
from unittest import TestCase, mock

from pywikibot import Site, Page
from testfixtures import compare

from tools import save_if_changed, add_category, has_fertig_category, has_korrigiert_category, remove_category
from tools.test import real_wiki_test


class TestTools(TestCase):
    def test_save_if_changed_positive(self):
        page_mock = mock.Mock()
        text_mock = mock.PropertyMock()
        type(page_mock).text = text_mock
        text_mock.return_value = "2"
        save_if_changed(page_mock, "1", "changed")
        compare(mock.call.save("changed", bot=True), page_mock.mock_calls[0])

    def test_save_if_changed_negativ(self):
        page_mock = mock.Mock()
        text_mock = mock.PropertyMock()
        type(page_mock).text = text_mock
        text_mock.return_value = "1"
        save_if_changed(page_mock, "1", "changed")
        compare(0, len(page_mock.mock_calls))

        save_if_changed(page_mock, "1 ", "changed")
        compare(0, len(page_mock.mock_calls))

    def test_add_category(self):
        compare("test\n[[Kategorie:new_cat]]", add_category("test", "new_cat"))

    def test_add_category_already_there(self):
        compare("test\n[[Kategorie:new_cat]]", add_category("test\n[[Kategorie:new_cat]]", "new_cat"))

    def test_remove_category(self):
        compare("test", remove_category("test\n[[Kategorie:new_cat]]", "new_cat"))

    @real_wiki_test
    def test__has_category(self):
        WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
        page = Page(WS_WIKI, "Seite:Meyers b11 s0001.jpg")
        compare(True, has_fertig_category(page))
        compare(False, has_korrigiert_category(page))
