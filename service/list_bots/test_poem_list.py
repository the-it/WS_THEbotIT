# pylint: disable=protected-access,line-too-long
from unittest import mock, skip

import pywikibot
from ddt import ddt, file_data
from testfixtures import compare

from service.list_bots.poem_list import PoemList
from tools.bots.cloud.test_base import TestCloudBase
from tools.test import real_wiki_test, PageMock


@ddt
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

    def test_get_print_title(self):
        compare("[[lemma]]", self.poem_list.get_print_title({"title": "lemma", "lemma": "lemma"}))
        compare("[[lemma|title]]", self.poem_list.get_print_title({"title": "title", "lemma": "lemma"}))
        compare("data-sort-value=\"lemma #Das\"|[[lemma|Das lemma]]", self.poem_list.get_print_title({"title": "Das lemma", "lemma": "lemma", "sortkey": "lemma #Das"}))

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
        given = {"author": "", "sortkey_auth": ""}
        compare("", self.poem_list.get_print_author(given))
        given = {"author": "Someone", "sortkey_auth": "Someone", "no_lemma_auth": "yes"}
        compare("Someone", self.poem_list.get_print_author(given))

    def test_get_year(self):
        compare("1920", self.poem_list.get_year({"creation": "1920", "publish": "1930"}))
        compare("1930", self.poem_list.get_year({"creation": "", "publish": "1930"}))
        compare("", self.poem_list.get_year({"creation": "", "publish": ""}))
        compare("1234", self.poem_list.get_year({"creation": "[1234]"}))
        compare("data-sort-value=\"1919-12-12\"|12. Dezember 1919", self.poem_list.get_year({"creation": "12. Dezember 1919"}))

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
                        'year': 'data-sort-value="1785-11-00"|November 1785',
                        'first_name': 'Friedrich',
                        'last_name': 'Schiller',
                        'lemma': 'An die Freude (Schiller)',
                        'sortkey': 'An die Freude.',
                        'sortkey_auth': 'Schiller, Friedrich',
                        'title': 'An die Freude.',
                        'first_line': 'Freude, schöner Götterfunken,'
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
                'year': '',
                'first_name': 'Johann Wolfgang',
                'last_name': 'von Goethe',
                'lemma': 'Mayfest (Johann Wolfgang von Goethe)',
                'sortkey': 'Mayfest (Johann Wolfgang von Goethe)',
                'sortkey_auth': 'Goethe, Johann Wolfgang von',
                'title': '',
                'first_line': 'Wie herrlich leuchtet',
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
                'year': '',
                'first_name': 'Johann Wolfgang',
                'last_name': 'von Goethe',
                'lemma': 'Mayfest (Johann Wolfgang von Goethe)',
                'sortkey': 'Mayfest',
                'sortkey_auth': 'Goethe, Johann Wolfgang von',
                'first_line': 'Wie herrlich leuchtet',
                'title': 'Mayfest'
            }, poem_dict)

    @real_wiki_test
    def test_enrich_trash_in_author(self):
        lemma = pywikibot.Page(self.wiki, "Die wilden Gänse (Fallersleben)")
        poem_list = PoemList(self.wiki)
        poem_dict = {"lemma": lemma.title(),
                     "author": "[[August Heinrich Hoffmann von Fallersleben]] (Henricus Custos)"}
        poem_list.enrich_dict(lemma, poem_dict)
        compare('August Heinrich Hoffmann von Fallersleben', poem_dict["author"])

    @real_wiki_test
    def test_enrich_redirect(self):
        lemma = pywikibot.Page(self.wiki, "Ein Kehlkopf")
        poem_list = PoemList(self.wiki)
        poem_dict = {"lemma": lemma.title(), "author": "[[Hans Bötticher]]<br />(Joachim Ringelnatz)"}
        poem_list.enrich_dict(lemma, poem_dict)
        compare('Joachim Ringelnatz', poem_dict["author"])

    @file_data("test_data/test_get_first_line.yml")
    def test_get_first_line(self, given, expect):
        compare(expect, self.poem_list.get_first_line(given))

    #@skip("only for testing")
    def test_get_first_line_develop(self):
        text = """{{BRU|Die Gartenlaube (1888) b 153.jpg|center|500|||center}}


{{center|'''Abendlandschaft.'''}}


<poem>
Der Hirt bläst seine Weise,
Von fern ein Schuß noch fällt,
Die Wälder rauschen leise
Und Ströme tief im Feld.

Nur hinter jenem Hügel
Noch spielt der Abendschein –
O hätt’ ich, hätt’ ich Flügel,
Zu fliegen da hinein!
</poem>
{{AlR|'''J. v. Eichendorff.'''}}
        """
        compare("Der Hirt bläst seine Weise,", self.poem_list.get_first_line(text))

    @skip("only for testing")
    @real_wiki_test
    def test_integration_testing(self):
        lemma_mock = mock.patch("service.list_bots.poem_list.PoemList.get_lemma_list",
                                new_callable=mock.MagicMock).start()
        mock.patch("service.list_bots.author_list.Page.save").start()
        lemma_mock.return_value = ([":Ein Kehlkopf"], 1)
        self.addCleanup(mock.patch.stopall)
        with PoemList(self.wiki) as bot:
            bot.data.assign_dict({})
            bot.run()
            print(bot.data._data)

    def test_get_sortkey(self):
        compare("Zahnfleischkranke #Der",
                self.poem_list.get_sortkey({"lemma": "A", "title": "B"},
                                           "{{SORTIERUNG:Zahnfleischkranke #Der}}\n[[Kategorie:Joachim Ringelnatz]]"))
        compare("Zahnfleischkranke #Der",
                self.poem_list.get_sortkey({"lemma": "Der Zahnfleischkranke", "title": ""},
                                           "[[Kategorie:Joachim Ringelnatz]]"))
        compare("Zahnfleischkranke #Der",
                self.poem_list.get_sortkey({"lemma": "Die Zahnfleischkranke", "title": "Der Zahnfleischkranke"},
                                           "[[Kategorie:Joachim Ringelnatz]]"))

    def test_get_page_info_gartenlaube(self):
        text = """{{GartenlaubenArtikel
|VORIGER=
|TITEL=1870
|NÄCHSTER=Frühlingsboten
|AUTOR=[[Friedrich Hofmann]]
|JAHR=1880
|Heft=33
|Seite=529
|BILD=
|KURZBESCHREIBUNG=
|WIKIPEDIA=
|SONSTIGES=
|BEARBEITUNGSSTAND=fertig
}}

{{BlockSatzStart}}
{{SeitePR|529|Die Gartenlaube (1880) 529.jpg|1}}
{{BlockSatzEnd}}

[[Kategorie:Friedrich Hofmann]]
[[Kategorie:Gedicht]]"""
        page = PageMock()
        page.text = text
        compare(
            {
                "title": "1870",
                "author": "[[Friedrich Hofmann]]",
                "publish": "1880",
            },
            self.poem_list.get_page_infos(page))

    @real_wiki_test
    def test_get_page_info_kapitel(self):
        poem_list = PoemList(self.wiki)
        page = pywikibot.Page(self.wiki, "Hände (Březina)/*")
        compare(
            {
                "title": "*",
                "author": "[[Otokar Březina]]",
                "publish": "1908",
                "creation": "",
            },
            poem_list.get_page_infos(page))

    def test_get_page_info_kapitel_wrong_slash(self):
        text = """{{Kapitel
|ANMERKUNG=Origninaltitel: *
|HERKUNFT=Hände (Březina)
|VORIGER=Orte der Harmonie und der Versöhnung
|NÄCHSTER=Frauen
|TITELTEIL=2
|WIKIPEDIA=
|BEARBEITUNGSSTAND=fertig
|KATEGORIE=Brezina Hände 1908
|SEITE=57
}}"""
        page = PageMock()
        page.text = text
        page.title_str = "Something_without_a_slash"
        with self.assertRaisesRegex(ValueError, "Referenced part of the title doesn't exists for Something_without_a_slash"):
            self.poem_list.get_page_infos(page)

    def test_get_page_info_kapitel_parent_does_not_exist(self):
        text = """{{Kapitel
|ANMERKUNG=Origninaltitel: *
|HERKUNFT=Hände (Březina)
|VORIGER=Orte der Harmonie und der Versöhnung
|NÄCHSTER=Frauen
|TITELTEIL=2
|WIKIPEDIA=
|BEARBEITUNGSSTAND=fertig
|KATEGORIE=Brezina Hände 1908
|SEITE=57
}}"""
        page = PageMock()
        page.text = text
        page.title_str = "Parent/chapter"
        poem_list = PoemList(self.wiki)
        with self.assertRaisesRegex(ValueError, "Page Parent as parent page for Parent/chapter does not exist"):
            poem_list.get_page_infos(page)
