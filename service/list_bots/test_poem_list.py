# pylint: disable=protected-access,line-too-long
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

    def test_print_list(self):
        self.fail()

    def test_get_print_title(self):
        compare("lemma", self.poem_list.get_print_title({"title": "lemma", "lemma": "lemma"}))
        compare("lemma|title", self.poem_list.get_print_title({"title": "title", "lemma": "lemma"}))
        compare("lemma|lemma NO TITLE", self.poem_list.get_print_title({"title": "", "lemma": "lemma"}))


    def test_get_print_author(self):
        given = {"author": "Karl Marx"}
        compare("[[Karl Marx]]", self.poem_list.get_print_author(given))
        given = {"author": "Karl Marx", "first_name": "Karl"}
        compare("[[Karl Marx|Karl]]", self.poem_list.get_print_author(given))
        given = {"author": "Karl Marx", "last_name": "Marx"}
        compare("[[Karl Marx|Marx]]", self.poem_list.get_print_author(given))
        given = {"author": "Karl Marx", "last_name": "Marx", "first_name": "Karl"}
        compare("[[Karl Marx|Marx, Karl]]", self.poem_list.get_print_author(given))
        given = {"author": "Karl Marx", "sortkey_auth": "Kommunismus"}
        compare("data-sort-value=\"Kommunismus\"|[[Karl Marx|Karl Marx]]", self.poem_list.get_print_author(given))

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
                        'sortkey': 'An die Freude.',
                        'publish': '1786',
                        'sortkey_auth': 'Schiller, Friedrich',
                        'title': 'An die Freude.'
                    }
                },
                bot.data._data
            )

    @real_wiki_test
    def test_enrich_author(self):
        lemma = pywikibot.Page(self.wiki, "Mayfest (Johann Wolfgang von Goethe)")
        poem_list = PoemList(self.wiki)
        poem_dict = {"lemma": lemma.title(), "author": "Johann Wolfgang von Goethe"}
        poem_list.enrich_dict(lemma, poem_dict)
        compare(
            {
                'author': 'Johann Wolfgang von Goethe',
                'creation': '',
                'first_name': 'Johann Wolfgang',
                'last_name': 'von Goethe',
                'lemma': 'Mayfest (Johann Wolfgang von Goethe)',
                'publish': '',
                'sortkey': 'Mayfest (Johann Wolfgang von Goethe)',
                'sortkey_auth': 'Goethe, Johann Wolfgang von',
                'title': ''
            }, poem_dict)

        poem_dict = {
            "lemma": lemma.title(),
            "title": "Mayfest",
            "author": "Johann Wolfgang von Goethe"
        }
        poem_list.enrich_dict(lemma, poem_dict)
        compare(
            {
                'author': 'Johann Wolfgang von Goethe',
                'creation': '',
                'first_name': 'Johann Wolfgang',
                'last_name': 'von Goethe',
                'lemma': 'Mayfest (Johann Wolfgang von Goethe)',
                'publish': '',
                'sortkey': 'Mayfest',
                'sortkey_auth': 'Goethe, Johann Wolfgang von',
                'title': 'Mayfest'
            }, poem_dict)
