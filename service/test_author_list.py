# pylint: disable=protected-access,line-too-long
from unittest import mock

from ddt import file_data, ddt
from pywikibot.scripts.generate_user_files import pywikibot
from testfixtures import compare

from service.author_list import AuthorListNew
from tools.bots.cloud.test_base import TestCloudBase
from tools.test import real_wiki_test


@ddt
class TestAuthorList(TestCloudBase):
    wiki = pywikibot.Site(code="de", fam="wikisource", user="THEbotIT")

    def setUp(self):
        self.author_list = AuthorListNew()

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
    def test_integration(self):
        lemma_mock = mock.patch("service.author_list.AuthorListNew.get_lemma_list",
                                new_callable=mock.MagicMock).start()
        mock.patch("service.author_list.Page.save").start()
        lemma_mock.return_value = ([":Willy_Stöwer"], 1)
        self.addCleanup(mock.patch.stopall)
        with AuthorListNew(self.wiki) as bot:
            bot.data.assign_dict({"checked": {}, "authors": {}})
            bot.run()
            compare(
                {":Willy_Stöwer":
                    {
                        "title": "Willy Stöwer",
                        "first_name": "Willy",
                        "last_name": "Stöwer",
                        "birth": "22. Mai 1864",
                        "death": "31. Mai 1931",
                        "sortkey": "Stöwer, Willy",
                        "description": "Maler, Illustrator"
                    }
                },
                bot.data._data["authors"]
            )

    @real_wiki_test
    def test_enrich(self):
        lemma = pywikibot.Page(self.wiki, "Willy Stöwer")
        author_dict = {}
        self.author_list.enrich_author_dict(author_dict, lemma)
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
        self.author_list.enrich_author_dict(author_dict, data_item)
        compare("Eschenbach, Wolfram", author_dict["sortkey"])

    @real_wiki_test
    def test_enrich_zinke_has_no_data_item(self):
        lemma = pywikibot.Page(self.wiki, "Gustav Zinke")
        author_dict = {"last_name": "Zinke", }
        self.author_list.enrich_author_dict(author_dict, lemma)
        compare("Zinke", author_dict["sortkey"])

    @real_wiki_test
    def test_enrich_both_names_must_be_missing(self):
        lemma = pywikibot.Page(self.wiki, "Willy Stöwer")
        author_dict = {"last_name": "Stöwer"}
        self.author_list.enrich_author_dict(author_dict, lemma)
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
        self.author_list.enrich_author_dict(author_dict, lemma)
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
        self.author_list.enrich_author_dict(author_dict, lemma)
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
        claim = self.author_list.get_highest_claim(data_item, "P735")
        compare(claim.getTarget().get()["labels"]["de"], "Aristoteles")

    @real_wiki_test
    def test_get_highest_claim_get_preferred(self):
        lemma = pywikibot.Page(self.wiki, "Aristoteles")
        data_item = lemma.data_item()
        claim = self.author_list.get_highest_claim(data_item, "P106")
        compare(claim.getTarget().get()["labels"]["de"], "Philosoph")

    @real_wiki_test
    def test_get_value_aristoteles(self):
        data_item = pywikibot.Page(self.wiki, "Aristoteles").data_item()

        claim = data_item.text["claims"]["P734"][0]
        value = self.author_list.get_value_from_claim(claim)
        compare(value, None)

        claim = data_item.text["claims"]["P735"][0]
        value = self.author_list.get_value_from_claim(claim)
        compare(value, "Aristoteles")

    @real_wiki_test
    def test_get_value_hartung(self):
        data_item = pywikibot.Page(self.wiki, "Johannes Hartung").data_item()

        claim = data_item.text["claims"]["P570"][0]
        value = self.author_list.get_value_from_claim(claim)
        compare(value, None)

    @real_wiki_test
    def test_get_value_achenwall(self):
        data_item = pywikibot.Page(self.wiki, "Gottfried Achenwall").data_item()

        claim = data_item.text["claims"]["P734"][0]
        value = self.author_list.get_value_from_claim(claim)
        compare(value, "Achenwall")

    @real_wiki_test
    def test_get_value_waldemar(self):
        data_item = pywikibot.Page(self.wiki, "Falscher Waldemar").data_item()

        claim = data_item.text["claims"]["P569"][0]
        value = self.author_list.get_value_from_claim(claim)
        compare(value, None)

    @real_wiki_test
    def test_enrisch_wunschmann(self):
        lemma = pywikibot.Page(self.wiki, "Ernst Wunschmann")
        author_dict = {}
        self.author_list.enrich_author_dict(author_dict, lemma)
        compare(
            "",
            author_dict["death"])

    @real_wiki_test
    def test_get_highest_claim_Reizer(self):
        data_item = pywikibot.Page(self.wiki, "Johann Georg Reizer").data_item()
        compare(None, self.author_list.get_highest_claim(data_item, "P570"))

    @real_wiki_test
    def test_get_value_dates(self):
        data_item = pywikibot.Page(self.wiki, "Aristoteles").data_item()

        claim = data_item.text["claims"]["P570"][0]
        value = self.author_list.get_value_from_claim(claim)
        compare(value, "322 v. Chr.")

        claim = data_item.text["claims"]["P570"][1]
        value = self.author_list.get_value_from_claim(claim)
        compare(value, "7. März 322 v. Chr.")

        data_item = pywikibot.Page(self.wiki, "Walther von der Vogelweide").data_item()
        claim = data_item.text["claims"]["P569"][0]
        value = self.author_list.get_value_from_claim(claim)
        compare(value, "1170")

        data_item = pywikibot.Page(self.wiki, "Theokrit").data_item()
        claim = data_item.text["claims"]["P569"][0]
        value = self.author_list.get_value_from_claim(claim)
        compare(value, "4. Jh. v. Chr.")

        data_item = pywikibot.Page(self.wiki, "Fritz Herbert Alma").data_item()
        claim = data_item.text["claims"]["P570"][0]
        value = self.author_list.get_value_from_claim(claim)
        compare(value, "Dezember 1981")

    def test_sorting(self):
        self.author_list.data.assign_dict(
            {"authors":
                {
                    "A (second one)": {
                        "title": "A (second one)",
                        "sortkey": "A",
                        "birth": "2.1.1900",
                        "death": "2.1.2000"
                    },
                    "B": {
                        "title": "B",
                        "sortkey": "B",
                        "birth": "3.3.2000"
                        ,
                        "death": "3.3.2100"
                    },
                    "A (first one)": {
                        "title": "A (first one)",
                        "sortkey": "A",
                        "birth": "1.1.1900",
                        "death": "1.1.2000"
                    }
                }
            }
        )
        compare(
            [
                {
                    "title": "A (first one)",
                    "sortkey": "A",
                    "birth": "1.1.1900",
                    "birth_sort": "1900-01-01",
                    "death": "1.1.2000",
                    "death_sort": "2000-01-01",
                },
                {
                    "title": "A (second one)",
                    "sortkey": "A",
                    "birth": "2.1.1900",
                    "birth_sort": "1900-01-02",
                    "death": "2.1.2000",
                    "death_sort": "2000-01-02",
                },
                {
                    "title": "B",
                    "sortkey": "B",
                    "birth": "3.3.2000",
                    "birth_sort": "2000-03-03",
                    "death": "3.3.2100",
                    "death_sort": "2100-03-03",
                }
            ],
            self.author_list.sort_to_list()
        )

    def test_printing(self):
        self.author_list.data.assign_dict({"authors": {}})
        test_list = [
            {
                "title": "A (first one)",
                "sortkey": "A",
                "first_name": "A",
                "last_name": "AA",
                "birth": "1.1.1900",
                "birth_sort": "1900-01-01",
                "death": "1.1.2000",
                "death_sort": "2000-01-01",
                "description": "A (first one)",
            },
            {
                "title": "A (second one)",
                "sortkey": "A",
                "first_name": "A",
                "birth": "2.1.1900",
                "birth_sort": "1900-01-02",
                "death": "2.1.2000",
                "death_sort": "2000-01-02",
                "description": "A (second one)"
            },
            {
                "title": "B",
                "sortkey": "B",
                "last_name": "BB",
                "birth": "3.3.2000",
                "birth_sort": "2000-03-03",
                "death": "3.3.2100",
                "death_sort": "2100-03-03",
                "description": "B",
            }
        ]

        compare(
            """Die Liste kann mit den Buttons neben den Spaltenüberschriften nach der jeweiligen Spalte sortiert werden.
<!--
Diese Liste wurde durch ein Computerprogramm erstellt, das die Daten verwendet, die aus den Infoboxen auf den Autorenseiten stammen.
Sollten daher Fehler vorhanden sein, sollten diese jeweils dort korrigiert werden.
-->
{{Tabellenstile}}
{|class="wikitable sortable tabelle-kopf-fixiert"
!style="width:20%"| Name
!data-sort-type="text" style="width:15%"| Geb.-datum
!data-sort-type="text" style="width:15%"| Tod.-datum
!class="unsortable" style="width:50%"| Beschreibung
|-
|data-sort-value="A"|[[A (first one)|AA, A]]
|data-sort-value="1900-01-01"|1.1.1900
|data-sort-value="2000-01-01"|1.1.2000
|A (first one)
|-
|data-sort-value="A"|[[A (second one)|A]]
|data-sort-value="1900-01-02"|2.1.1900
|data-sort-value="2000-01-02"|2.1.2000
|A (second one)
|-
|data-sort-value="B"|[[B|BB]]
|data-sort-value="2000-03-03"|3.3.2000
|data-sort-value="2100-03-03"|3.3.2100
|B
|}

== Anmerkungen ==
<references/>

{{SORTIERUNG:Autoren #Liste der}}
[[Kategorie:Listen]]
[[Kategorie:Autoren|!]]""" in self.author_list.print_author_list(test_list),
            True)
