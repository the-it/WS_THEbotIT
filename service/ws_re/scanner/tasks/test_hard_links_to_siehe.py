from testfixtures import compare

from service.ws_re.register.repo import DataRepo
from service.ws_re.register.test_base import clear_tst_path, copy_tst_data
from service.ws_re.scanner.tasks.hard_links_to_siehe import HLTSTask
from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.template.re_page import RePage


class TestHLTSTask(TaskTestCase):
    @classmethod
    def setUpClass(cls):
        DataRepo.mock_data(True)
        clear_tst_path()

    @classmethod
    def tearDownClass(cls):
        clear_tst_path(renew_path=False)
        DataRepo.mock_data(False)

    def setUp(self):
        super().setUp()
        copy_tst_data("I_1_base", "I_1")
        copy_tst_data("authors", "authors")
        copy_tst_data("authors_mapping", "authors_mapping")
        self.task = HLTSTask(None, self.logger)

    def test_replacements_in_article_text(self):
        self.page_mock.title_str = "RE:Quelllemma"
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
        compare({("Leben(a)", "Quelllemma")}, self.task._unknown_targets)  # pylint: disable=protected-access

    def test_replacements_in_plain_text_segments(self):
        self.page_mock.text = (
            "Vorab [[RE:Leben(a)|Leben]].\n{{REDaten}}\nText im Artikel.\n{{REAutor|Autor.}}\nNachlauf [[RE:Leben(b)]]."
        )
        re_page = RePage(self.page_mock)

        result = self.task.run(re_page)
        compare({"success": True, "changed": True}, result)

        full_text = str(re_page)
        self.assertIn("Vorab {{RE siehe|Leben(a)|Leben}}.", full_text)
        self.assertIn("Nachlauf {{RE siehe|Leben(b)}}.", full_text)

    def test_hardlink_gets_display_text_when_lemma_in_register(self):
        self.page_mock.text = """{{REDaten}}
Text mit Links: [[RE:Aal]] und [[RE:Aarassos|Leben]].
{{REAutor|Autor.}}"""
        re_page = RePage(self.page_mock)

        result = self.task.run(re_page)
        compare({"success": True, "changed": True}, result)
        self.assertIn("[[RE:Aal|Aal]]", re_page[0].text)
        self.assertIn("[[RE:Aarassos|Leben]]", re_page[0].text)

    def test_hardlink_for_register_lemma_with_underscore_or_lowercase_gets_display_text(self):
        self.page_mock.text = """{{REDaten}}
Links: [[RE:Aba_1]] und [[RE:aba 2]].
{{REAutor|Autor.}}"""
        re_page = RePage(self.page_mock)

        result = self.task.run(re_page)
        compare({"success": True, "changed": True}, result)
        self.assertIn("[[RE:Aba_1|Aba_1]]", re_page[0].text)
        self.assertIn("[[RE:aba 2|aba 2]]", re_page[0].text)

    def test_no_replacement_for_links_with_anchor(self):
        self.page_mock.text = """{{REDaten}}
Text mit Link: [[RE:Leben(a)#Abschnitt]].
{{REAutor|Autor.}}"""
        re_page = RePage(self.page_mock)

        result = self.task.run(re_page)
        compare({"success": True, "changed": False}, result)
        self.assertIn("[[RE:Leben(a)#Abschnitt]]", re_page[0].text)

    def test_siehe_converted_to_hardlink_when_lemma_in_register(self):
        self.page_mock.text = """{{REDaten}}
Text mit Vorlagen: {{RE siehe|Aal}} und {{RE siehe|Aarassos|Leben}}.
{{REAutor|Autor.}}"""
        re_page = RePage(self.page_mock)

        result = self.task.run(re_page)
        compare({"success": True, "changed": True}, result)

        after = re_page[0].text
        self.assertIn("[[RE:Aal|Aal]]", after)
        self.assertIn("[[RE:Aarassos|Leben]]", after)
        self.assertNotIn("{{RE siehe|Aal}}", after)
        self.assertNotIn("{{RE siehe|Aarassos|Leben}}", after)

    def test_no_change_when_no_hard_links_present(self):
        self.page_mock.text = """{{REDaten}}
Im Text stehen nur Vorlagen: {{RE siehe|Anderes(a)|Leben}}.
{{REAutor|Autor.}}"""
        re_page = RePage(self.page_mock)
        result = self.task.run(re_page)
        compare({"success": True, "changed": False}, result)
