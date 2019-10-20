# pylint: disable=protected-access
from unittest import mock

from testfixtures import compare

from scripts.service.ws_re.scanner import DEWPTask
from scripts.service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from scripts.service.ws_re.template.re_page import RePage

_BASE_TASK_PYWIKIBOT_PAGE = "scripts.service.ws_re.scanner.tasks.base_task.pywikibot.Page"


class TestDEWPTask(TaskTestCase):
    def test_link_is_missing(self):
        with mock.patch(_BASE_TASK_PYWIKIBOT_PAGE, new_callable=mock.MagicMock) as page_mock:
            self.text_mock.return_value = """{{REDaten
|WP=Bla
}}
{{REAutor|Autor.}}"""
            self.title_mock.return_value = "Re:Title"
            page_mock.return_value.exists.side_effect = [False]
            re_page = RePage(self.page_mock)
            task = DEWPTask(None, self.logger)
            compare({"success": True, "changed": False}, task.run(re_page))
            compare({"not_exists": [("Bla", "Title")], "redirect": []}, task.data)

    def test_link_is_existend(self):
        with mock.patch(_BASE_TASK_PYWIKIBOT_PAGE, new_callable=mock.MagicMock) as page_mock:
            self.text_mock.return_value = """{{REDaten
|WP=Bla
}}
{{REAutor|Autor.}}"""
            self.title_mock.return_value = "Re:Title"
            page_mock.return_value.exists.side_effect = [True]
            page_mock.return_value.isRedirectPage.side_effect = [False]
            re_page = RePage(self.page_mock)
            task = DEWPTask(None, self.logger)
            compare({"success": True, "changed": False}, task.run(re_page))
            compare({"not_exists": [], "redirect":[]}, task.data)

    def test_link_is_existend_but_redirect(self):
        with mock.patch(_BASE_TASK_PYWIKIBOT_PAGE, new_callable=mock.MagicMock) as page_mock:
            self.text_mock.return_value = """{{REDaten
|WP=Bla
}}
{{REAutor|Autor.}}"""
            self.title_mock.return_value = "Re:Title"
            page_mock.return_value.exists.side_effect = [True]
            page_mock.return_value.isRedirectPage.side_effect = [True]
            re_page = RePage(self.page_mock)
            task = DEWPTask(None, self.logger)
            compare({"success": True, "changed": False}, task.run(re_page))
            compare({"not_exists": [], "redirect": [("Bla", "Title")]}, task.data)

    def test_link_several_links(self):
        with mock.patch(_BASE_TASK_PYWIKIBOT_PAGE, new_callable=mock.MagicMock) as page_mock:
            self.text_mock.return_value = """{{REDaten|WP=Bla}}
{{REAutor|Autor.}}

{{REDaten|WP=Blub}}
{{REAutor|Autor.}}

{{REDaten}}
{{REAutor|Autor.}}

{{REDaten|WP=Blab}}
{{REAutor|Autor.}}

{{REDaten|WP=Blob}}
{{REAutor|Autor.}}"""
            self.title_mock.return_value = "Re:Title"
            page_mock.return_value.exists.side_effect = [True, False, False, True]
            page_mock.return_value.isRedirectPage.side_effect = [False, True]
            re_page = RePage(self.page_mock)
            task = DEWPTask(None, self.logger)
            compare({"success": True, "changed": False}, task.run(re_page))
            compare({"not_exists": [("Blub", "Title"), ("Blab", "Title")], "redirect":[("Blob", "Title")]}, task.data)

            self.text_mock.return_value = """{{REDaten|WP=Bli}}
{{REAutor|Autor.}}"""
            self.title_mock.return_value = "Re:Title2"
            page_mock.return_value.exists.side_effect = [False]
            re_page = RePage(self.page_mock)
            compare({"success": True, "changed": False}, task.run(re_page))
            compare({"not_exists": [("Blub", "Title"), ("Blab", "Title"), ("Bli", "Title2")],
                     "redirect": [("Blob", "Title")]}, task.data)

    def test_build_entries(self):
        task = DEWPTask(None, self.logger)
        task.data = {"not_exists": [("One", "First_Lemma"), ("Two", "Second_Lemma")],
                     "redirect": [("Three", "Second_Lemma")]}
        expect = [
            "=== Artikel existieren in Wikipedia nicht ===",
            "* Wikpedia Artikel: [[w:One]] (verlinkt von [[RE:First_Lemma]]) existiert nicht",
            "* Wikpedia Artikel: [[w:Two]] (verlinkt von [[RE:Second_Lemma]]) existiert nicht",
            "=== Linkziel ist ein Redirect ===",
            "* Wikpedia Artikel: [[w:Three]] (verlinkt von [[RE:Second_Lemma]]) ist ein Redirect",
                  ]
        compare(expect, task._build_entry().split("\n")[-5:])

    def test_data_exists(self):
        task = DEWPTask(None, self.logger)
        task.data = {"not_exists": [("One", "First_Lemma")],
                     "redirect": []}
        self.assertTrue(task._data_exists())
        task.data = {"not_exists": [],
                     "redirect": [("One", "First_Lemma")]}
        self.assertTrue(task._data_exists())
        task.data = {"not_exists": [],
                     "redirect": []}
        self.assertFalse(task._data_exists())
