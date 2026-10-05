from unittest import TestCase
from unittest.mock import MagicMock

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
                "description": "deutscher Marinemaler der Kaiserzeit",
            },
            author_dict,
        )

    @real_wiki_test
    def test_enrich_eschenbach(self):
        lemma = pywikibot.Page(self.wiki, "Wolfram von Eschenbach")
        data_item = lemma.data_item()
        author_dict = {
            "first_name": "Wolfram",
            "last_name": "von Eschenbach",
        }
        self.author_info.enrich_author_dict(author_dict, data_item)
        compare("Eschenbach, Wolfram", author_dict["sortkey"])

    @real_wiki_test
    def test_enrich_zinke_has_no_data_item(self):
        lemma = pywikibot.Page(self.wiki, "Gustav Zinke")
        author_dict = {
            "last_name": "Zinke",
        }
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
                "description": "deutscher Marinemaler der Kaiserzeit",
            },
            author_dict,
        )

        author_dict = {"first_name": "Willy"}
        self.author_info.enrich_author_dict(author_dict, lemma)
        compare(
            {
                "first_name": "Willy",
                "birth": "22. Mai 1864",
                "death": "31. Mai 1931",
                "sortkey": "Willy",
                "description": "deutscher Marinemaler der Kaiserzeit",
            },
            author_dict,
        )

        author_dict = {}
        self.author_info.enrich_author_dict(author_dict, lemma)
        compare(
            {
                "first_name": "Willy",
                "last_name": "Stöwer",
                "birth": "22. Mai 1864",
                "death": "31. Mai 1931",
                "sortkey": "Stöwer, Willy",
                "description": "deutscher Marinemaler der Kaiserzeit",
            },
            author_dict,
        )

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
        compare("", author_dict["death"])

    @real_wiki_test
    def test_enrich_aristoteles(self):
        lemma = pywikibot.Page(self.wiki, "Aristoteles")
        author_dict = {}
        self.author_info.enrich_author_dict(author_dict, lemma)
        compare("Aristoteles", author_dict["sortkey"])
        compare("", author_dict["last_name"])

    @real_wiki_test
    def test_get_highest_claim_Reizer(self):
        data_item = pywikibot.Page(self.wiki, "Johann Georg Reizer").data_item()
        compare(None, self.author_info.get_highest_claim(data_item, "P570"))

    @staticmethod
    def _time_claim(year: int, precision: int, month: int = 1, day: int = 1) -> MagicMock:
        claim = MagicMock()
        claim.type = "time"
        claim.getTarget.return_value = MagicMock(year=year, month=month, day=day, precision=precision)
        return claim

    def test_get_value_dates(self):
        compare(None, self.author_info.get_value_from_claim(self._time_claim(-1000, 6)))
        compare("12. Jh.", self.author_info.get_value_from_claim(self._time_claim(1150, 7)))
        compare("4. Jh. v. Chr.", self.author_info.get_value_from_claim(self._time_claim(-400, 7)))
        compare("1170", self.author_info.get_value_from_claim(self._time_claim(1170, 9)))
        compare("322 v. Chr.", self.author_info.get_value_from_claim(self._time_claim(-322, 9)))
        compare("Dezember 1981", self.author_info.get_value_from_claim(self._time_claim(1981, 10, month=12)))
        compare(
            "7. März 322 v. Chr.", self.author_info.get_value_from_claim(self._time_claim(-322, 11, month=3, day=7))
        )
        compare("6. Dezember 1981", self.author_info.get_value_from_claim(self._time_claim(1981, 11, month=12, day=6)))

    def test_get_value_dates_no_target(self):
        claim = MagicMock()
        claim.type = "time"
        claim.getTarget.return_value = None
        compare(None, self.author_info.get_value_from_claim(claim))

    @real_wiki_test
    def test_get_value_dates_real_claim(self):
        data_item = pywikibot.Page(self.wiki, "Aristoteles").data_item()

        claim = data_item.text["claims"]["P570"][0]
        value = self.author_info.get_value_from_claim(claim)
        compare(value, "322 v. Chr.")

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
            AuthorInfo(lemma).get_author_dict(),
        )
