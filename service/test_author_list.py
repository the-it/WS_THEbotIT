# pylint: disable=protected-access
from unittest import TestCase, mock

from ddt import file_data, ddt
from pywikibot.scripts.generate_user_files import pywikibot
from testfixtures import compare

from service.author_list import AuthorListNew
from tools.bots.cloud.test_base import TestCloudBase
from tools.test import real_wiki_test


@ddt
class TestProtect(TestCloudBase):
    def setUp(self):
        self.author_list = AuthorListNew()

    #     self.petscan_mock = mock.patch("service.protect.PetScan").start()
    #     self.get_combined_lemma_list_mock = mock.Mock()
    #     self.petscan_mock.return_value = mock.Mock(get_combined_lemma_list=self.get_combined_lemma_list_mock)
    #     self.page_mock = mock.patch("service.protect.Page", new_callable=mock.MagicMock).start()
    #     self.protect_mock = mock.Mock()
    #     self.page_mock.return_value = mock.Mock(protect=self.protect_mock)
    #     self.addCleanup(mock.patch.stopall)

    # def tearDown(self):
    #     mock.patch.stopall()
    #

    @file_data("test_data/test_get_page_infos.yml")
    def test_get_page_infos(self, given, expect):
        compare(expect, self.author_list.get_page_infos(given))

    def test_get_page_infos_errors(self):
        with self.assertRaises(ValueError):
            self.author_list.get_page_infos("")
        with self.assertRaises(ValueError):
            self.author_list.get_page_infos("{{Personendaten")
        with self.assertRaises(ValueError):
            self.author_list.get_page_infos("{{Personendaten}}\n{{Personendaten}}")

    @real_wiki_test
    def test_enrich(self):
        WS_WIKI = pywikibot.Site(code="de", fam="wikisource", user="THEbotIT")
        lemma = pywikibot.Page(WS_WIKI, "Willy Stöwer")
        data_item = lemma.data_item()
        author_dict = {}
        self.author_list.enrich_author_dict(author_dict, data_item)
        compare({"first_name": "Willy",
                 "last_name": "Stöwer",
                 "birth": "22. Mai 1864",
                 "death": "31. Mai 1931"}, author_dict)

    @real_wiki_test
    def test_enrich_both_names_must_be_missing(self):
        WS_WIKI = pywikibot.Site(code="de", fam="wikisource", user="THEbotIT")
        lemma = pywikibot.Page(WS_WIKI, "Willy Stöwer")
        data_item = lemma.data_item()
        author_dict = {"last_name": "Stöwer"}
        self.author_list.enrich_author_dict(author_dict, data_item)
        compare({"last_name": "Stöwer",
                       "birth": "22. Mai 1864",
                       "death": "31. Mai 1931"}, author_dict)

        author_dict = {"first_name": "Willy"}
        self.author_list.enrich_author_dict(author_dict, data_item)
        compare({"first_name": "Willy",
                       "birth": "22. Mai 1864",
                       "death": "31. Mai 1931"}, author_dict)

        author_dict = {}
        self.author_list.enrich_author_dict(author_dict, data_item)
        compare({"first_name": "Willy",
                       "last_name": "Stöwer",
                       "birth": "22. Mai 1864",
                       "death": "31. Mai 1931"}, author_dict)

    @real_wiki_test
    def test_get_highest_claim_filter_out(self):
        WS_WIKI = pywikibot.Site(code="de", fam="wikisource", user="THEbotIT")
        lemma = pywikibot.Page(WS_WIKI, "Aristoteles")
        data_item = lemma.data_item()
        claim = self.author_list.get_highest_claim(data_item, "P735")
        compare(claim.getTarget().get()["labels"]["de"], "Aristoteles")

    @real_wiki_test
    def test_get_highest_claim_get_preferred(self):
        WS_WIKI = pywikibot.Site(code="de", fam="wikisource", user="THEbotIT")
        lemma = pywikibot.Page(WS_WIKI, "Aristoteles")
        data_item = lemma.data_item()
        claim = self.author_list.get_highest_claim(data_item, "P106")
        compare(claim.getTarget().get()["labels"]["de"], "Philosoph")

    @real_wiki_test
    def test_get_value_aristoteles(self):
        WS_WIKI = pywikibot.Site(code="de", fam="wikisource", user="THEbotIT")
        data_item = pywikibot.Page(WS_WIKI, "Aristoteles").data_item()

        claim = data_item.text["claims"]["P734"][0]
        value = self.author_list.get_value_from_claim(claim)
        compare(value, None)

        claim = data_item.text["claims"]["P735"][0]
        value = self.author_list.get_value_from_claim(claim)
        compare(value, "Aristoteles")

    @real_wiki_test
    def test_get_value_dates(self):
        WS_WIKI = pywikibot.Site(code="de", fam="wikisource", user="THEbotIT")
        data_item = pywikibot.Page(WS_WIKI, "Aristoteles").data_item()

        claim = data_item.text["claims"]["P570"][0]
        value = self.author_list.get_value_from_claim(claim)
        compare(value, "322 v. Chr.")

        claim = data_item.text["claims"]["P570"][1]
        value = self.author_list.get_value_from_claim(claim)
        compare(value, "7. März 322 v. Chr.")

        data_item = pywikibot.Page(WS_WIKI, "Walther von der Vogelweide").data_item()
        claim = data_item.text["claims"]["P569"][0]
        value = self.author_list.get_value_from_claim(claim)
        compare(value, "1170")

        data_item = pywikibot.Page(WS_WIKI, "Theokrit").data_item()
        claim = data_item.text["claims"]["P569"][0]
        value = self.author_list.get_value_from_claim(claim)
        compare(value, "4. Jh. v. Chr.")

        data_item = pywikibot.Page(WS_WIKI, "Fritz Herbert Alma").data_item()
        claim = data_item.text["claims"]["P570"][0]
        value = self.author_list.get_value_from_claim(claim)
        compare(value, "Dezember 1981")
