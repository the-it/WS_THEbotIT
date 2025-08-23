# pylint: disable=protected-access
from unittest import mock

import pywikibot
from testfixtures import compare

from service.ws_re.scanner.tasks.death_wp_links import DEWPTask
from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.template.re_page import RePage

_BASE_TASK_PYWIKIBOT_PAGE = "service.ws_re.scanner.tasks.base_task.pywikibot.Page"


class TestDEWPTask(TaskTestCase):
    def test_link_is_missing(self):
        with mock.patch(_BASE_TASK_PYWIKIBOT_PAGE, new_callable=mock.MagicMock) as page_mock:
            self.page_mock.text = """{{REDaten
|WP=Bla
}}
{{REAutor|Autor.}}"""
            self.page_mock.title_str = "Re:Title"
            page_mock.return_value.exists.side_effect = [False]
            re_page = RePage(self.page_mock)
            task = DEWPTask(None, self.logger)
            compare({"success": True, "changed": False}, task.run(re_page))
            compare({"not_exists": [("Bla", "Title")], "redirect": [], "disambiguous": []}, task.data)

    def test_link_is_existend(self):
        with mock.patch(_BASE_TASK_PYWIKIBOT_PAGE, new_callable=mock.MagicMock) as page_mock:
            self.page_mock.text = """{{REDaten
|WP=Bla
}}
{{REAutor|Autor.}}"""
            self.page_mock.title_str = "Re:Title"
            page_mock.return_value.exists.side_effect = [True]
            page_mock.return_value.isDisambig.side_effect = [False]
            page_mock.return_value.isRedirectPage.side_effect = [False]
            re_page = RePage(self.page_mock)
            task = DEWPTask(None, self.logger)
            compare({"success": True, "changed": False}, task.run(re_page))
            compare({"not_exists": [], "redirect":[], "disambiguous": []}, task.data)

    def test_link_is_existend_but_redirect(self):
        with mock.patch(_BASE_TASK_PYWIKIBOT_PAGE, new_callable=mock.MagicMock) as page_mock:
            self.page_mock.text = """{{REDaten
|WP=Bla
}}
{{REAutor|Autor.}}"""
            self.page_mock.title_str = "Re:Title"
            page_mock.return_value.exists.side_effect = [True]
            page_mock.return_value.isRedirectPage.side_effect = [True]
            re_page = RePage(self.page_mock)
            task = DEWPTask(None, self.logger)
            compare({"success": True, "changed": False}, task.run(re_page))
            compare({"not_exists": [], "redirect": [("Bla", "Title")], "disambiguous": []}, task.data)

    def test_link_is_existend_but_disambiguous(self):
        with mock.patch(_BASE_TASK_PYWIKIBOT_PAGE, new_callable=mock.MagicMock) as page_mock:
            self.page_mock.text = """{{REDaten
|WP=Bla
}}
{{REAutor|Autor.}}"""
            self.page_mock.title_str = "Re:Title"
            page_mock.return_value.exists.side_effect = [True]
            page_mock.return_value.isRedirectPage.side_effect = [False]
            page_mock.return_value.isDisambig.side_effect = [True]
            re_page = RePage(self.page_mock)
            task = DEWPTask(None, self.logger)
            compare({"success": True, "changed": False}, task.run(re_page))
            compare({"not_exists": [], "redirect": [], "disambiguous": [("Bla", "Title")]}, task.data)

    def test_link_several_links(self):
        with mock.patch(_BASE_TASK_PYWIKIBOT_PAGE, new_callable=mock.MagicMock) as page_mock:
            self.page_mock.text = """{{REDaten|WP=Bla}}
{{REAutor|Autor.}}

{{REDaten|WP=Blub}}
{{REAutor|Autor.}}

{{REDaten}}
{{REAutor|Autor.}}

{{REDaten|WP=Blab}}
{{REAutor|Autor.}}

{{REDaten|WP=Blob}}
{{REAutor|Autor.}}

{{REDaten|WP=Bleb}}
{{REAutor|Autor.}}"""
            self.page_mock.title_str = "Re:Title"
            page_mock.return_value.exists.side_effect = [True, False, False, True, True]
            page_mock.return_value.isRedirectPage.side_effect = [False, True, False]
            page_mock.return_value.isDisambig.side_effect = [False, True]
            re_page = RePage(self.page_mock)
            task = DEWPTask(None, self.logger)
            compare({"success": True, "changed": False}, task.run(re_page))
            compare({"not_exists": [("Blub", "Title"), ("Blab", "Title")],
                     "redirect":[("Blob", "Title")],
                     "disambiguous": [("Bleb", "Title")]},
                    task.data)

            self.page_mock.text = """{{REDaten|WP=Bli}}
{{REAutor|Autor.}}"""
            self.page_mock.title_str = "Re:Title2"
            page_mock.return_value.exists.side_effect = [False]
            re_page = RePage(self.page_mock)
            compare({"success": True, "changed": False}, task.run(re_page))
            compare({"not_exists": [("Blub", "Title"), ("Blab", "Title"), ("Bli", "Title2")],
                     "redirect": [("Blob", "Title")], "disambiguous": [("Bleb", "Title")]}, task.data)

    def test_build_entries(self):
        task = DEWPTask(None, self.logger)
        task.data = {"not_exists": [("One", "First_Lemma"), ("Two", "Second_Lemma")],
                     "redirect": [("Three", "Second_Lemma")],
                     "disambiguous": [("Four", "Second_Lemma")]}
        expect = [
            "=== Artikel existieren in Wikipedia nicht ===",
            "* Wikipedia-Artikel: [[w:One]] (verlinkt von [[RE:First_Lemma]]) existiert nicht",
            "* Wikipedia-Artikel: [[w:Two]] (verlinkt von [[RE:Second_Lemma]]) existiert nicht",
            "=== Linkziel ist ein Redirect ===",
            "* Wikipedia-Artikel: [[w:Three]] (verlinkt von [[RE:Second_Lemma]]) ist ein Redirect",
            "=== Linkziel ist eine Begriffsklärungsseite ===",
            "* Wikipedia-Artikel: [[w:Four]] (verlinkt von [[RE:Second_Lemma]]) ist eine Begriffsklärungsseite",
            ]
        compare(expect, task._build_entry().split("\n")[-7:])

    def test_data_exists(self):
        task = DEWPTask(None, self.logger)
        task.data = {"not_exists": [("One", "First_Lemma")],
                     "redirect": [],
                     "disambiguous": []}
        self.assertTrue(task._data_exists())
        task.data = {"not_exists": [],
                     "redirect": [("One", "First_Lemma")],
                     "disambiguous": []}
        self.assertTrue(task._data_exists())
        task.data = {"not_exists": [],
                     "redirect": [],
                     "disambiguous": [("One", "First_Lemma")]}
        self.assertTrue(task._data_exists())
        task.data = {"not_exists": [],
                     "redirect": [],
                     "disambiguous": []}
        self.assertFalse(task._data_exists())

    def test_bug_invalid_title(self):
        with mock.patch(_BASE_TASK_PYWIKIBOT_PAGE, new_callable=mock.MagicMock) as page_mock:
            self.page_mock.text = """{{REDaten|WP=<!-- Nicht Megiddo -->}}
{{REAutor|Autor.}}"""
            self.page_mock.title_str = "Re:Title"
            page_mock.return_value.exists.side_effect = \
                pywikibot.exceptions.InvalidTitleError("contains illegal char(s) '<'")
            re_page = RePage(self.page_mock)
            task = DEWPTask(None, self.logger)
            compare({"success": True, "changed": False}, task.run(re_page))
            compare({"not_exists": [('<!-- Nicht Megiddo -->', 'Title')], "redirect": [], "disambiguous": []},
                    task.data)
