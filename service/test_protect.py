# pylint: disable=protected-access
import time
from datetime import timedelta
from unittest import mock

import pywikibot
from testfixtures import compare

from service.protect import Protect
from tools.bots.test_base import TestCloudBase
from tools.test import real_wiki_test


class TestProtect(TestCloudBase):
    def setUp(self):
        self.petscan_mock = mock.patch("service.protect.PetScan").start()
        self.get_combined_lemma_list_mock = mock.Mock()
        self.petscan_mock.return_value = mock.Mock(get_combined_lemma_list=self.get_combined_lemma_list_mock)
        self.page_mock = mock.patch("service.protect.Page", new_callable=mock.MagicMock).start()
        self.protect_mock = mock.Mock()
        self.page_mock.return_value = mock.Mock(protect=self.protect_mock)
        self.addCleanup(mock.patch.stopall)

    def tearDown(self):
        mock.patch.stopall()

    def test_init(self):
        self.get_combined_lemma_list_mock.return_value = ([":lemma"], 1)
        self.page_mock.return_value.categories.return_value = ["Kategorie:Fertig"]
        with Protect(wiki=None, debug=False, log_to_wiki=False) as bot:
            bot.run()

    def test_page_already_protected(self):
        self.get_combined_lemma_list_mock.return_value = ([":lemma"], 1)
        self.page_mock.return_value.protection.return_value = {'move': 'autoconfirmed', 'edit': 'autoconfirmed'}
        self.page_mock.return_value.categories.return_value = ["Kategorie:Fertig"]
        with Protect(wiki=None, debug=False, log_to_wiki=False) as bot:
            bot.run()
        self.protect_mock.assert_not_called()

    def test_page_not_protected(self):
        self.get_combined_lemma_list_mock.return_value = ([":lemma"], 1)
        self.page_mock.return_value.protection.return_value = {}  # no protection
        self.page_mock.return_value.categories.return_value = ["Kategorie:Fertig"]
        with Protect(wiki=None, debug=False, log_to_wiki=False) as bot:
            bot.run()
        self.protect_mock.assert_called_once_with(reason= "Schutz fertiger Seiten",
                                                  protections={'move': 'autoconfirmed', 'edit': 'autoconfirmed'})

    def test_3_pages_one_is_protected(self):
        self.get_combined_lemma_list_mock.return_value = ([":lemma1", "Seite:lemma2", "Index:Lemma3"], 3)
        self.page_mock.return_value.protection.side_effect = [{}, {"something": "something"}, {}]
        self.page_mock.return_value.categories.return_value = ["Kategorie:Fertig"]
        with Protect(wiki=None, debug=False, log_to_wiki=False) as bot:
            bot.run()
        compare(2, self.protect_mock.call_count)

    def test_3_pages_one_isnt_fertig_anymore(self):
        self.get_combined_lemma_list_mock.return_value = ([":lemma1", "Seite:lemma2", "Index:Lemma3"], 3)
        self.page_mock.return_value.protection.return_value = {}
        self.page_mock.return_value.categories.side_effect = [[], ["Kategorie:Fertig"], ["Kategorie:Fertig"]]
        with Protect(wiki=None, debug=False, log_to_wiki=False) as bot:
            bot.data.assign_dict({":lemma1": "20110101010101", "Seite:lemma2": "20110101010101"})
            bot.run()
        compare(["Seite:lemma2", "Index:Lemma3"], list(bot.data.keys()))
        compare(2, self.protect_mock.call_count)

    def test_timeout(self):
        self.get_combined_lemma_list_mock.return_value = ([":lemma1", "Seite:lemma2", "Index:Lemma3"], 3)
        self.page_mock.return_value.protection.return_value = {}  # no protection
        self.page_mock.return_value.categories.return_value = ["Kategorie:Fertig"]
        with Protect(wiki=None, debug=False, log_to_wiki=False) as bot:
            bot.timeout = timedelta(milliseconds=1)
            time.sleep(0.002)
            bot.run()
        compare(1, self.protect_mock.call_count)  # only first lemma was protected, after that timeout hit

    @real_wiki_test
    @staticmethod
    def test_has_fertig_cat():
        WS_WIKI = pywikibot.Site(code="de", fam="wikisource", user="THEbotIT")
        lemma = pywikibot.Page(WS_WIKI, "Benutzter:THEprotectIT")
        compare(False, Protect._has_fertig_cat(lemma))
        lemma = pywikibot.Page(WS_WIKI, "Seite:Die Gartenlaube (1855) 465.jpg")
        compare(True, Protect._has_fertig_cat(lemma))
