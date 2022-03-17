# pylint: disable=protected-access,no-self-use
from unittest import mock, skip

import pywikibot
from testfixtures import compare

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
        self.page_fetcher_mock = mock.patch("service.ws_re.scanner.tasks.add_short_description."
                                            "KURZTask._get_short_description_text_from_source").start()
        self.alphabet_mock = mock.patch("service.ws_re.scanner.tasks.add_short_description.RE_ALPHABET",
                                        ["a", "z"]).start()
        self.page_fetcher_mock.return_value = TEXT_A
        self.addCleanup(mock.patch.stopall)

    def tearDown(self):
        mock.patch.stopall()

    def test_load_from_source_pages(self):
        task = KURZTask(None, self.logger)
        self.page_fetcher_mock.side_effect = [TEXT_A, TEXT_Z]
        union_dict = task._load_short_descriptions()
        compare(union_dict["Aachen"], "deutsche Stadt = Aquae")
        compare(union_dict["Zaa"], "Volk Aithiopiens")
        compare(4, len(union_dict))

    def test_load_short_descriptions_from_text(self):
        short_text_lookup = KURZTask._parse_short_description(TEXT_A)
        compare(short_text_lookup, {"Aachen": "deutsche Stadt = Aquae", "Aal": "Zoologisch"})

    def test_add_short_description_to_lemma(self):
        self.text_mock.return_value = """{{REDaten}}
text
{{REAutor|Autor.}}"""
        self.title_mock.return_value = "Re:Aachen"
        re_page = RePage(self.page_mock)
        task = KURZTask(None, self.logger)
        compare({"success": True, "changed": True}, task.run(re_page))
        compare("deutsche Stadt = Aquae", re_page.first_article["KURZTEXT"].value)
        compare("text\n[[Kategorie:RE:Kurztext überprüfen]]", re_page.first_article.text)

    def test_existing_short_description_to_lemma(self):
        self.text_mock.return_value = """{{REDaten
|KURZTEXT=Test}}
{{REAutor|Autor.}}"""
        self.title_mock.return_value = "Re:Aachen"
        re_page = RePage(self.page_mock)
        task = KURZTask(None, self.logger)
        compare({"success": True, "changed": False}, task.run(re_page))
        compare("Test", re_page.first_article["KURZTEXT"].value)


@skip("only for analysis")
class TestKURZTaskProcessSourceLoadReality(TaskTestCase):
    def test_load_real_sources(self):
        task = KURZTask(pywikibot.Site(code='de', fam='wikisource', user='THEbotIT'), self.logger)
        self.assertGreater(len(task.short_description_lookup), 14000)
