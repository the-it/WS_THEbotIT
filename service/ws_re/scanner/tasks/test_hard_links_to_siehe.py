from testfixtures import compare

from service.ws_re.scanner.tasks.hard_links_to_siehe import HLTSTask
from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.template.re_page import RePage


class TestHLTSTask(TaskTestCase):
    def setUp(self):
        super().setUp()
        self.task = HLTSTask(None, self.logger)

    def test_replacements_in_article_text(self):
        self.page_mock.text = """{{REDaten
}}
Text mit Links: [[RE:Leben(a)]] und [[RE:Leben(a)|Leben]].
{{REAutor|Autor.}}"""
        re_page = RePage(self.page_mock)

        result = self.task.run(re_page)
        compare({"success": True, "changed": True}, result)

        after = re_page[0].text
        self.assertIn("{{RE siehe|Leben(a)}}", after)
        self.assertIn("{{RE siehe|Leben(a)|Leben}}", after)
        self.assertNotIn("[[RE:Leben(a)]]", after)
        self.assertNotIn("[[RE:Leben(a)|Leben]]", after)

    def test_replacements_in_plain_text_segments(self):
        self.page_mock.text = (
            "Vorab [[RE:Leben(a)|Leben]].\n{{REDaten}}\nText im Artikel.\n{{REAutor|Autor.}}\nNachlauf [[RE:Leben(a)]]."
        )
        re_page = RePage(self.page_mock)

        result = self.task.run(re_page)
        compare({"success": True, "changed": True}, result)

        full_text = str(re_page)
        self.assertIn("Vorab {{RE siehe|Leben(a)|Leben}}.", full_text)
        self.assertIn("Nachlauf {{RE siehe|Leben(a)}}.", full_text)

    def test_no_change_when_no_hard_links_present(self):
        self.page_mock.text = """{{REDaten}}
Im Text stehen nur Vorlagen: {{RE siehe|Anderes(a)|Leben}}.
{{REAutor|Autor.}}"""
        re_page = RePage(self.page_mock)
        result = self.task.run(re_page)
        compare({"success": True, "changed": False}, result)
