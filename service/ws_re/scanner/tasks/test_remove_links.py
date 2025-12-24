from testfixtures import compare

from service.ws_re.scanner.tasks.remove_links import RELITask
from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.template.re_page import RePage


class TestRELITask(TaskTestCase):
    def setUp(self):
        super().setUp()
        # ensure default target list is known for tests
        RELITask.TARGET_LEMMAS = ["Leben(a)"]
        self.task = RELITask(None, self.logger)

    def test_replacements_in_article_text(self):
        # Build a page with one article whose text contains all three patterns
        self.page_mock.text = """{{REDaten
}}
Text mit Mustern: {{RE siehe|Leben(a)|Leben}}, {{RE siehe|Leben(a)}}, [[RE:Leben(a)|Leben]].
Und ein Nicht-Treffer: {{RE siehe|Anderes(a)|Leben}} und [[RE:Anderes(a)|Leben]].
{{REAutor|Autor.}}"""
        re_page = RePage(self.page_mock)

        # Sanity pre-condition
        before = re_page[0].text
        self.assertIn("{{RE siehe|Leben(a)|Leben}}", before)
        self.assertIn("{{RE siehe|Leben(a)}}", before)
        self.assertIn("[[RE:Leben(a)|Leben]]", before)

        result = self.task.run(re_page)

        # Verify task ran and detected change
        compare({"success": True, "changed": True}, result)

        after = re_page[0].text
        # Expected replacements
        self.assertIn("Text mit Mustern: Leben, Leben(a), Leben.", after)
        # Non-target lemma should remain unchanged
        self.assertIn("{{RE siehe|Anderes(a)|Leben}}", after)
        self.assertIn("[[RE:Anderes(a)|Leben]]", after)

    def test_replacements_in_plain_text_segments(self):
        # Put the pattern outside of any Article blocks to hit string segments
        self.page_mock.text = (
            "Vorab [[RE:Leben(a)|Leben]] und {{RE siehe|Leben(a)|Leben}}.\n"
            "{{REDaten}}\nText im Artikel.\n{{REAutor|Autor.}}\n"
            "Nachlauf {{RE siehe|Leben(a)}}."
        )
        re_page = RePage(self.page_mock)

        # Run task
        result = self.task.run(re_page)
        compare({"success": True, "changed": True}, result)

        # Reconstruct full page text and verify replacements applied in non-Article parts
        full_text = str(re_page)
        self.assertIn("Vorab Leben und Leben.", full_text)
        self.assertIn("Nachlauf Leben(a).", full_text)

    def test_no_change_when_no_targets_present(self):
        self.page_mock.text = """{{REDaten}}
Im Text stehen andere Links: {{RE siehe|Anderes(a)|Leben}} und [[RE:Anderes(a)|Leben]].
{{REAutor|Autor.}}"""
        re_page = RePage(self.page_mock)
        result = self.task.run(re_page)
        compare({"success": True, "changed": False}, result)
