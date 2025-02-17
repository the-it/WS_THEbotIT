from unittest import TestCase

from ddt import file_data, ddt
import pywikibot
from testfixtures import compare

from service.list_bots.author_info import AuthorInfo
from tools.test import real_wiki_test


class TestAuthorInfo(TestCase):
    wiki = pywikibot.Site(code="de", fam="wikisource", user="THEbotIT")

    def setUp(self):
        self.author_info = AuthorInfo(None)

    @real_wiki_test
    def test_enrich(self):
        lemma = pywikibot.Page(self.wiki, "Willy Stöwer")
        author_dict = {}
        self.author_info.enrich_author_dict(author_dict, lemma)
        compare(
            {
                "first_name": "Willy",
                "last_name": "Stöwer",
                "birth": "22. Mai 1864",
                "death": "31. Mai 1931",
                "sortkey": "Stöwer, Willy",
                "description": "deutscher Marinemaler der Kaiserzeit"
            },
            author_dict)

    @real_wiki_test
    def test_enrich_eschenbach(self):
        lemma = pywikibot.Page(self.wiki, "Wolfram von Eschenbach")
        data_item = lemma.data_item()
        author_dict = {"first_name": "Wolfram", "last_name": "von Eschenbach", }
        self.author_info.enrich_author_dict(author_dict, data_item)
        compare("Eschenbach, Wolfram", author_dict["sortkey"])

    @real_wiki_test
    def test_enrich_zinke_has_no_data_item(self):
        lemma = pywikibot.Page(self.wiki, "Gustav Zinke")
        author_dict = {"last_name": "Zinke", }
        self.author_info.enrich_author_dict(author_dict, lemma)
        compare("Zinke", author_dict["sortkey"])

    @real_wiki_test
    def test_enrich_both_names_must_be_missing(self):
        lemma = pywikibot.Page(self.wiki, "Willy Stöwer")
        author_dict = {"last_name": "Stöwer"}
        self.author_info.enrich_author_dict(author_dict, lemma)
        compare(
            {
                "last_name": "Stöwer",
                "birth": "22. Mai 1864",
                "death": "31. Mai 1931",
                "sortkey": "Stöwer",
                "description": "deutscher Marinemaler der Kaiserzeit"
            },
            author_dict)

        author_dict = {"first_name": "Willy"}
        self.author_info.enrich_author_dict(author_dict, lemma)
        compare(
            {
                "first_name": "Willy",
                "birth": "22. Mai 1864",
                "death": "31. Mai 1931",
                "sortkey": "Willy",
                "description": "deutscher Marinemaler der Kaiserzeit"
            },
            author_dict)

        author_dict = {}
        self.author_info.enrich_author_dict(author_dict, lemma)
        compare(
            {
                "first_name": "Willy",
                "last_name": "Stöwer",
                "birth": "22. Mai 1864",
                "death": "31. Mai 1931",
                "sortkey": "Stöwer, Willy",
                "description": "deutscher Marinemaler der Kaiserzeit"
            },
            author_dict)

    @real_wiki_test
    def test_get_highest_claim_filter_out(self):
        lemma = pywikibot.Page(self.wiki, "Aristoteles")
        data_item = lemma.data_item()
        claim = self.author_info.get_highest_claim(data_item, "P735")
        compare(claim.getTarget().get()["labels"]["de"], "Aristoteles")

    @real_wiki_test
    def test_get_highest_claim_get_preferred(self):
        lemma = pywikibot.Page(self.wiki, "Aristoteles")
        data_item = lemma.data_item()
        claim = self.author_info.get_highest_claim(data_item, "P106")
        compare(claim.getTarget().get()["labels"]["de"], "Philosoph")

    @real_wiki_test
    def test_get_value_aristoteles(self):
        data_item = pywikibot.Page(self.wiki, "Aristoteles").data_item()

        claim = data_item.text["claims"]["P734"][0]
        value = self.author_info.get_value_from_claim(claim)
        compare(value, None)

        claim = data_item.text["claims"]["P735"][0]
        value = self.author_info.get_value_from_claim(claim)
        compare(value, "Aristoteles")

    @real_wiki_test
    def test_get_value_hartung(self):
        data_item = pywikibot.Page(self.wiki, "Johannes Hartung").data_item()

        claim = data_item.text["claims"]["P570"][0]
        value = self.author_info.get_value_from_claim(claim)
        compare(value, None)

    @real_wiki_test
    def test_get_value_achenwall(self):
        data_item = pywikibot.Page(self.wiki, "Gottfried Achenwall").data_item()

        claim = data_item.text["claims"]["P734"][0]
        value = self.author_info.get_value_from_claim(claim)
        compare(value, "Achenwall")

    @real_wiki_test
    def test_get_value_waldemar(self):
        data_item = pywikibot.Page(self.wiki, "Falscher Waldemar").data_item()

        claim = data_item.text["claims"]["P569"][0]
        value = self.author_info.get_value_from_claim(claim)
        compare(value, None)

    @real_wiki_test
    def test_enrich_wunschmann(self):
        lemma = pywikibot.Page(self.wiki, "Ernst Wunschmann")
        author_dict = {}
        self.author_info.enrich_author_dict(author_dict, lemma)
        compare(
            "",
            author_dict["death"])

    @real_wiki_test
    def test_get_highest_claim_Reizer(self):
        data_item = pywikibot.Page(self.wiki, "Johann Georg Reizer").data_item()
        compare(None, self.author_info.get_highest_claim(data_item, "P570"))

    @real_wiki_test
    def test_get_value_dates(self):
        data_item = pywikibot.Page(self.wiki, "Aristoteles").data_item()

        claim = data_item.text["claims"]["P570"][0]
        value = self.author_info.get_value_from_claim(claim)
        compare(value, "322 v. Chr.")

        claim = data_item.text["claims"]["P570"][1]
        value = self.author_info.get_value_from_claim(claim)
        compare(value, "7. März 322 v. Chr.")

        data_item = pywikibot.Page(self.wiki, "Walther von der Vogelweide").data_item()
        claim = data_item.text["claims"]["P569"][0]
        value = self.author_info.get_value_from_claim(claim)
        compare(value, "1170")

        data_item = pywikibot.Page(self.wiki, "Theokrit").data_item()
        claim = data_item.text["claims"]["P569"][0]
        value = self.author_info.get_value_from_claim(claim)
        compare(value, "4. Jh. v. Chr.")

        data_item = pywikibot.Page(self.wiki, "Fritz Herbert Alma").data_item()
        claim = data_item.text["claims"]["P570"][0]
        value = self.author_info.get_value_from_claim(claim)
        compare(value, "Dezember 1981")

    @real_wiki_test
    def test_end_to_end(self):
        lemma = pywikibot.Page(self.wiki, "Willy Stöwer")
        compare(
            {
                "first_name": "Willy",
                "last_name": "Stöwer",
                "birth": "22. Mai 1864",
                "death": "31. Mai 1931",
                "sortkey": "Stöwer, Willy",
                "description": "Maler, Illustrator",
            },
            AuthorInfo(lemma).get_author_dict())
