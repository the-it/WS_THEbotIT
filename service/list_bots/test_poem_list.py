# pylint: disable=protected-access,line-too-long
from unittest import mock, skip, TestCase

import pywikibot
from ddt import ddt, file_data
from testfixtures import compare

from service.list_bots.poem_list import PoemList
from tools.bots.cloud.test_base import TestCloudBase
from tools.test import real_wiki_test


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
                        'title': 'An die Freude.',
                        'first_line': ''
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
                'creation': '',
                'first_name': 'Johann Wolfgang',
                'last_name': 'von Goethe',
                'lemma': 'Mayfest (Johann Wolfgang von Goethe)',
                'publish': '',
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

    @skip("only for testing")
    def test_get_first_line_develop(self):
        text = """
{{LineCenterSize|140|22|'''Vorwort'''}}



<center>
{|
|colspan="3"|
|-
|{{idt}}
|
<poem>
Ach, was muß man oft von bösen<!-- first_line -->
Kindern hören oder lesen!!
Wie zum Beispiel hier von diesen,
Welche Max und Moritz hießen;
</poem>
|
|-
|colspan="3"|
[[Bild:Max und Moritz (Busch) 001.png|300px|center]]
|-
|
|align="left"|
<poem>
{{Zeile|5}}Die, anstatt durch weise Lehren
Sich zum Guten zu bekehren,
Oftmals noch darüber lachten
Und sich heimlich lustig machten. –
– Ja, zur Übeltätigkeit,
{{Zeile|10}}Ja, dazu ist man bereit! –
– Menschen necken, Tiere quälen,
Äpfel, Birnen, Zwetschen stehlen – –
Das ist freilich angenehmer
Und dazu auch viel bequemer,
{{Zeile|15}}Als in Kirche oder Schule
Festzusitzen auf dem Stuhle. –
– Aber wehe, wehe, wehe!
Wenn ich, auf das Ende sehe!! –
– Ach, das war ein schlimmes Ding,
{{Zeile|20}}Wie es Max und Moritz ging.
– Drum ist hier, was sie getrieben,
Abgemalt und aufgeschrieben.
</poem>
|}
</center>

== Inhalt ==
* '''[[Max und Moritz/Erster Streich|Erster Streich]]'''
* '''[[Max und Moritz/Zweiter Streich|Zweiter Streich]]'''
* '''[[Max und Moritz/Dritter Streich|Dritter Streich]]'''
* '''[[Max und Moritz/Vierter Streich|Vierter Streich]]'''
* '''[[Max und Moritz/Fünfter Streich|Fünfter Streich]]'''
* '''[[Max und Moritz/Sechster Streich|Sechster Streich]]'''
* '''[[Max und Moritz/Letzter Streich|Letzter Streich]]'''

[[Kategorie:Kinderlyrik]]
[[Kategorie:Neuhochdeutsch]]
        """
        compare("Ach, was muß man oft von bösen<!-- first_line -->", self.poem_list.get_first_line(text))

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
