from unittest import mock

import pywikibot
from testfixtures import compare

from service.list_bots.poem_list import PoemList
from tools.bots.cloud.test_base import TestCloudBase
from tools.test import real_wiki_test


class TestPoemList(TestCloudBase):
    wiki = pywikibot.Site(code="de", fam="wikisource", user="THEbotIT")

    def setUp(self):
        self.poem_list = PoemList()

    def test_sort_to_list(self):
        self.poem_list.data.assign_dict(
            {
                "A (second one)": {
                    "lemma": "A (second one)",
                    "sortkey": "A"
                },
                "B": {
                    "lemma": "B",
                    "sortkey": "B"
                },
                "A (first one)": {
                    "lemma": "A (first one)",
                    "sortkey": "A"
                }
            }
        )
        compare(
            [
                {
                    "lemma": "A (first one)",
                    "sortkey": "A",
                },
                {
                    "lemma": "A (second one)",
                    "sortkey": "A",
                },
                {
                    "lemma": "B",
                    "sortkey": "B",
                }
            ],
            self.poem_list.sort_to_list()
        )

    def test_enrich_dict(self):
        self.fail()

    def test_print_list(self):
        self.fail()

    def test_get_print_title(self):
        self.fail()

    def test_get_print_author(self):
        self.fail()

    def test_get_print_year(self):
        compare("1920", self.poem_list.get_print_year({"creation": "1920", "publish": "1930"}))
        compare("1930 (veröff.)", self.poem_list.get_print_year({"creation": "", "publish": "1930"}))
        compare("", self.poem_list.get_print_year({"creation": "", "publish": ""}))

    @real_wiki_test
    def test_integration(self):
        lemma_mock = mock.patch("service.list_bots.poem_list.PoemList.get_lemma_list",
                                new_callable=mock.MagicMock).start()
        mock.patch("service.list_bots.author_list.Page.save").start()
        lemma_mock.return_value = ([":An_die_Freude_(Schiller)"], 1)
        self.addCleanup(mock.patch.stopall)
        with PoemList(self.wiki) as bot:
            bot.data.assign_dict({})
            bot.run()
            del bot.data[":An_die_Freude_(Schiller)"]["check"]
            compare(
                {":An_die_Freude_(Schiller)":
                    {
                        'author': 'Friedrich Schiller',
                        'creation': 'November 1785',
                        'first_name': 'Friedrich',
                        'last_name': 'Schiller',
                        'lemma': 'An die Freude (Schiller)',
                        'publish': '1786',
                        'sortkey_auth': 'Schiller, Friedrich',
                        'title': 'An die Freude.'
                    }
                },
                bot.data._data
            )
