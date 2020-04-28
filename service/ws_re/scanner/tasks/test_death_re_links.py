# pylint: disable=protected-access
from pathlib import Path
from unittest import mock

from testfixtures import compare

from service.ws_re.scanner.tasks.death_re_links import DEALTask
from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.template.re_page import RePage

BASE_TASK_PYWIKIBOT_PAGE = "service.ws_re.scanner.tasks.base_task.pywikibot.Page"


class TestDEALTask(TaskTestCase):
    def test_process_next_previous(self):
        with mock.patch(BASE_TASK_PYWIKIBOT_PAGE, new_callable=mock.MagicMock) as page_mock:
            self.text_mock.return_value = """{{REDaten
|VG=Bla
|NF=Blub
}}
{{REAutor|Autor.}}"""
            self.title_mock.return_value = "Re:Title"
            page_mock.return_value.exists.side_effect = [True, False]
            re_page = RePage(self.page_mock)
            task = DEALTask(None, self.logger)
            compare({"success": True, "changed": False}, task.run(re_page))
            compare([("Blub", "Title")], task.data)

            self.text_mock.return_value = """{{REDaten
|VG=Bla
|NF=Blub
}}
{{REAutor|Autor.}}"""
            self.title_mock.return_value = "Re:Title2"
            page_mock.return_value.exists.side_effect = [False, True]
            re_page = RePage(self.page_mock)
            compare({"success": True, "changed": False}, task.run(re_page))
            compare([("Blub", "Title"), ("Bla", "Title2")], task.data)

    def test_process_next_previous_wrong_start_letter(self):
        with mock.patch(BASE_TASK_PYWIKIBOT_PAGE, new_callable=mock.MagicMock) as page_mock:
            self.text_mock.return_value = """{{REDaten
|VG=Bla
|NF=Episch
}}
{{REAutor|Autor.}}"""
            self.title_mock.return_value = "Re:Title"
            page_mock.return_value.exists.return_value = False
            re_page = RePage(self.page_mock)
            task = DEALTask(None, self.logger)
            compare({"success": True, "changed": False}, task.run(re_page))
            compare([("Bla", "Title")], task.data)

    def test_process_next_previous_multiple_aticles(self):
        with mock.patch(BASE_TASK_PYWIKIBOT_PAGE, new_callable=mock.MagicMock) as page_mock:
            self.text_mock.return_value = """{{REDaten
|VG=Bla
|NF=Episch
}}
{{REAutor|Autor.}}
{{REDaten
|VG=Blub
|NF=Chaos
}}
{{REAutor|Autor.}}"""
            self.title_mock.return_value = "Re:Title"
            page_mock.return_value.exists.return_value = False
            re_page = RePage(self.page_mock)
            task = DEALTask(None, self.logger)
            compare({"success": True, "changed": False}, task.run(re_page))
            compare([("Bla", "Title"), ("Blub", "Title"), ("Chaos", "Title")], task.data)

    def test_find_links_in_text(self):
        with mock.patch(BASE_TASK_PYWIKIBOT_PAGE, new_callable=mock.MagicMock) as page_mock:
            self.text_mock.return_value = """{{REDaten
}}
{{RE siehe|Aal}}
{{RE siehe|Anderer Quatsch}}
{{REAutor|Autor.}}"""
            self.title_mock.return_value = "Re:Title"
            page_mock.return_value.exists.side_effect = [True, False]
            re_page = RePage(self.page_mock)
            task = DEALTask(None, self.logger)
            compare({"success": True, "changed": False}, task.run(re_page))
            compare([("Anderer Quatsch", "Title")], task.data)

    def test_find_links_in_multiple_articles(self):
        with mock.patch(BASE_TASK_PYWIKIBOT_PAGE, new_callable=mock.MagicMock) as page_mock:
            self.text_mock.return_value = """{{REDaten}}
{{RE siehe|Aal}}
{{REAutor|Autor.}}
{{REDaten}}
{{RE siehe|Anderer Quatsch}}
{{REAutor|Autor.}}
{{REDaten}}
{{RE siehe|Besserer Quatsch}}
{{REAutor|Autor.}}
{{REDaten}}
{{RE siehe|Nicht hiernach suchen}}
{{REAutor|Autor.}}"""
            self.title_mock.return_value = "Re:Title"
            page_mock.return_value.exists.side_effect = [False, True, False, False]
            re_page = RePage(self.page_mock)
            task = DEALTask(None, self.logger)
            compare({"success": True, "changed": False}, task.run(re_page))
            compare([("Aal", "Title"), ("Besserer Quatsch", "Title")], task.data)

    def test_build_entries(self):
        task = DEALTask(None, self.logger)
        task.data = [("One", "First_Lemma"), ("Two", "Second_Lemma")]
        expect = ["* [[RE:One]] verlinkt von [[RE:First_Lemma]]",
                  "* [[RE:Two]] verlinkt von [[RE:Second_Lemma]]"]
        compare(expect, task._build_entry().split("\n")[-2:])

    def test_find_red_links(self):
        with mock.patch(BASE_TASK_PYWIKIBOT_PAGE, new_callable=mock.MagicMock) as page_mock:
            self.text_mock.return_value = """{{REDaten
}}
{{RE siehe|Aal}}
[[RE:Anderer Quatsch]]
{{REAutor|Autor.}}"""
            self.title_mock.return_value = "Re:Title"
            page_mock.return_value.exists.return_value = False
            re_page = RePage(self.page_mock)
            task = DEALTask(None, self.logger)
            compare({"success": True, "changed": False}, task.run(re_page))
            compare([("Aal", "Title"), ("Anderer Quatsch", "Title")], task.data)

    def test_value_exception_bug(self):
        with mock.patch(BASE_TASK_PYWIKIBOT_PAGE, new_callable=mock.MagicMock) as page_mock:
            with open(Path(__file__).parent.joinpath("test_data/bug_value_error_DEAL_task.txt"),
                      encoding="utf-8") as bug_file:
                self.text_mock.return_value = bug_file.read()
            self.title_mock.return_value = "Re:Caecilius 54a"
            page_mock.return_value.exists.return_value = False
            re_page = RePage(self.page_mock)
            task = DEALTask(None, self.logger)
            compare({"success": True, "changed": False}, task.run(re_page))
            expection = [('Caecilius 44', 'Caecilius 54a'),
                         ('Caecilius 57', 'Caecilius 54a'),
                         ('Arabia 1', 'Caecilius 54a'),
                         ('Aurelius 221', 'Caecilius 54a'),
                         ('Caecilius 54', 'Caecilius 54a')]
            compare(expection, task.data)
