# pylint: disable=protected-access,line-too-long
from unittest import mock

from pywikibot.scripts.generate_user_files import pywikibot
from testfixtures import compare

from service.list_bots.author_list import AuthorList
from tools.bots.cloud.test_base import TestCloudBase
from tools.test import real_wiki_test


class TestAuthorList(TestCloudBase):
    wiki = pywikibot.Site(code="de", fam="wikisource", user="THEbotIT")

    def setUp(self):
        self.author_list = AuthorList()

    def test_manual_date_sort(self):
        result = {"birth": "4. Dezember zwischen 1825 und 1850<!--1837-00-00-->",
                  "death": "frühestens 1916, spätestens 1921<!--1918-00-00-->", "sortkey": "Emilie Schröder"}

        self.author_list.data.assign_dict({"Emilie Schröder": result})
        sorted_list = self.author_list.sort_to_list()
        compare("1837-00-00", sorted_list[0]["birth_sort"])
        compare("1918-00-00", sorted_list[0]["death_sort"])

    @real_wiki_test
    def test_integration(self):
        lemma_mock = mock.patch("service.list_bots.author_list.PetScan.get_combined_lemma_list",
                                new_callable=mock.MagicMock).start()
        lemma_raw_mock = mock.patch("service.list_bots.author_list.PetScan.make_plain_list",
                                new_callable=mock.MagicMock).start()
        mock.patch("service.list_bots.author_list.Page.save").start()
        lemma_mock.return_value = ([":Willy_Stöwer", "something"], 2)
        lemma_raw_mock.return_value = [":Willy_Stöwer", "something"]
        self.addCleanup(mock.patch.stopall)
        with AuthorList(self.wiki) as bot:
            bot.data.assign_dict({})
            bot.run()
            del bot.data._data[":Willy_Stöwer"]["check"]
            del bot.data._data["something"]["check"]
            compare(
                {":Willy_Stöwer":
                    {
                        "lemma": "Willy Stöwer",
                        "first_name": "Willy",
                        "last_name": "Stöwer",
                        "birth": "22. Mai 1864",
                        "death": "31. Mai 1931",
                        "sortkey": "Stöwer, Willy",
                        "description": "Maler, Illustrator"
                    },
                    "something": {"lemma": "something"}
                },
                bot.data._data
            )


    def test_sorting(self):
        self.author_list.data.assign_dict(
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
        self.author_list.data.assign_dict({})
        test_list = [
            {
                "lemma": "A (first one)",
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
                "lemma": "A (second one)",
                "sortkey": "A",
                "first_name": "A",
                "birth": "2.1.1900",
                "birth_sort": "1900-01-02",
                "death": "2.1.2000",
                "death_sort": "2000-01-02",
                "description": "A (second one)"
            },
            {
                "lemma": "B",
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
[[Kategorie:Autoren|!]]""" in self.author_list.print_list(test_list),
            True)

    def test_get_check_list(self):
        self.author_list.data.assign_dict({"A": {"check": "2024"}, "B": {"check": "2023"}})
        compare({"A": "2024", "B": "2023"}, self.author_list.get_check_dict())

    def test_get_author_line(self):
        compare("B, A", self.author_list.get_author_line({"first_name": "A", "last_name": "B"}))
        compare("B", self.author_list.get_author_line({"first_name": "", "last_name": "B"}))
        compare("A", self.author_list.get_author_line({"first_name": "A", "last_name": ""}))
