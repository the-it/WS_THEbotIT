# pylint: disable=protected-access,no-self-use
from unittest import mock, skip

import pywikibot
from testfixtures import LogCapture, compare

from service.ws_re.scanner.tasks.add_short_description import KURZTask
from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.template.re_page import RePage

TEXT_A = """{|class="wikitable"
|-
!Artikel!!Kurzbeschreibung
|-
|[[RE:Aachen]]||deutsche Stadt = Aquae
|-
|[[RE:Aal]]||Zoologisch
|-
|[[RE:No real description]]||(-)
|-
|[[RE:Nothing to see]]||
|-
|[[RE:Ἀχαιῶν ἀκτή]]||Fancy greek stuff
|}"""

TEXT_Z = """
{|class="wikitable"
|-
!Artikel!!Kurzbeschreibung
|-
|[[RE:Zaa]]||Volk Aithiopiens
|-
|[[RE:Zaaram]]||Hauptstadt der Kinaidokolpitai an der W-Küste Arabiens
|}"""


class TestKURZTaskProcessSource(TaskTestCase):
    # pylint: disable=arguments-differ
    def setUp(self):
        super().setUp()  # pylint: disable=no-value-for-parameter
        self.page_fetcher_mock = mock.patch(
            "service.ws_re.scanner.tasks.add_short_description.KURZTask._get_short_description_text_from_source"
        ).start()
        self.alphabet_mock = mock.patch(
            "service.ws_re.scanner.tasks.add_short_description.RE_ALPHABET", ["a", "z"]
        ).start()
        self.page_fetcher_mock.return_value = TEXT_A
        self.addCleanup(mock.patch.stopall)

    def tearDown(self):
        mock.patch.stopall()

    def test_load_from_source_pages(self):
        task = KURZTask(None, self.logger)
        self.page_fetcher_mock.side_effect = [TEXT_A, TEXT_Z]
        union_dict = task._load_short_descriptions()
        compare(union_dict["aachen"], "deutsche Stadt = Aquae")
        compare(union_dict["zaa"], "Volk Aithiopiens")
        compare(5, len(union_dict))

    def test_load_short_descriptions_from_text(self):
        short_text_lookup = KURZTask._parse_short_description(TEXT_A)
        compare(
            short_text_lookup,
            {"aachen": "deutsche Stadt = Aquae", "aal": "Zoologisch", "achaion akte": "Fancy greek stuff"},
        )

    def test_add_short_description_to_lemma(self):
        self.page_mock.text = """{{REDaten}}
text
{{REAutor|Autor.}}"""
        self.page_mock.title_str = "Re:Aachen"
        re_page = RePage(self.page_mock)
        task = KURZTask(None, self.logger)
        compare({"success": True, "changed": True}, task.run(re_page))
        compare("deutsche Stadt = Aquae", re_page.first_article["KURZTEXT"].value)
        compare("[[Kategorie:RE:Kurztext überprüfen]]", re_page._article_list[-1])

    def test_add_short_description_to_lemma_sort_key(self):
        self.page_mock.text = """{{REDaten}}
text
{{REAutor|Autor.}}"""
        self.page_mock.title_str = "Re:Ἀχαιῶν akte"
        re_page = RePage(self.page_mock)
        task = KURZTask(None, self.logger)
        compare({"success": True, "changed": True}, task.run(re_page))
        compare("Fancy greek stuff", re_page.first_article["KURZTEXT"].value)
        compare("[[Kategorie:RE:Kurztext überprüfen]]", re_page._article_list[-1])

    def test_existing_short_description_to_lemma(self):
        self.page_mock.text = """{{REDaten
|KURZTEXT=Test}}
{{REAutor|Autor.}}"""
        self.page_mock.title_str = "Re:Aachen"
        re_page = RePage(self.page_mock)
        task = KURZTask(None, self.logger)
        compare({"success": True, "changed": False}, task.run(re_page))
        compare("Test", re_page.first_article["KURZTEXT"].value)

    def test_existing_verweis_dont_add(self):
        self.page_mock.text = """{{REDaten
|VERWEIS=ON}}
{{REAutor|Autor.}}"""
        self.page_mock.title_str = "Re:Aachen"
        re_page = RePage(self.page_mock)
        task = KURZTask(None, self.logger)
        compare({"success": True, "changed": False}, task.run(re_page))
        compare("", re_page.first_article["KURZTEXT"].value)

    def test_no_short_description_available(self):
        self.page_mock.text = """{{REDaten}}
text
{{REAutor|Autor.}}"""
        self.page_mock.title_str = "Re:Lemma without a short description"
        re_page = RePage(self.page_mock)
        task = KURZTask(None, self.logger)
        compare({"success": True, "changed": False}, task.run(re_page))
        compare("", re_page.first_article["KURZTEXT"].value)


class TestKURZTaskSourcePages(TaskTestCase):
    def setUp(self):
        super().setUp()
        mock.patch("service.ws_re.scanner.tasks.add_short_description.RE_ALPHABET", ["a"]).start()
        self.source_page_mock = mock.patch("service.ws_re.scanner.tasks.add_short_description.pywikibot.Page").start()
        self.addCleanup(mock.patch.stopall)

    def tearDown(self):
        mock.patch.stopall()

    def test_reads_the_lookup_from_the_source_page(self):
        self.source_page_mock.return_value.text = TEXT_A
        task = KURZTask(None, self.logger)
        compare("Zoologisch", task.short_description_lookup["aal"])
        compare("Wikisource:RE-Werkstatt/Kurzbeschreibung/a", self.source_page_mock.call_args[0][1])

    def test_logs_an_error_for_an_empty_source_page(self):
        self.source_page_mock.return_value.text = ""
        with LogCapture() as log_catcher:
            task = KURZTask(None, self.logger)
        compare({}, task.short_description_lookup)
        log_catcher.check_present(("Test", "ERROR", "Couldn't load Wikisource:RE-Werkstatt/Kurzbeschreibung/a."))


@skip("only for analysis")
class TestKURZTaskProcessSourceLoadReality(TaskTestCase):
    def test_load_real_sources(self):  # pragma: no cover
        task = KURZTask(pywikibot.Site(code="de", fam="wikisource", user="THEbotIT"), self.logger)
        self.assertGreater(len(task.short_description_lookup), 14000)
