# pylint: disable=protected-access
from unittest import mock

from ddt import ddt, file_data
from testfixtures import compare

from service.ws_re.scanner.tasks.death_re_links import DEALTask
from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.template.re_page import RePage

BASE_TASK_PYWIKIBOT_PAGE = "service.ws_re.scanner.tasks.base_task.pywikibot.Page"

@ddt
class TestDEALTask(TaskTestCase):
    def test_process_next_previous_process_two(self):
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

    @file_data("test_data/test_death_re_links.yml")
    def test_process(self, text, title, exists_mocks, expect):
        with mock.patch(BASE_TASK_PYWIKIBOT_PAGE, new_callable=mock.MagicMock) as page_mock:
            self.text_mock.return_value = text
            self.title_mock.return_value = title
            page_mock.return_value.exists.side_effect = exists_mocks
            re_page = RePage(self.page_mock)
            task = DEALTask(None, self.logger)
            compare({"success": True, "changed": False}, task.run(re_page))
            compare(expect, task.data)

    def test_build_entries(self):
        task = DEALTask(None, self.logger)
        task.data = [("One", "First_Lemma"), ("Two", "Second_Lemma")]
        expect = ["* [[RE:One]] verlinkt von [[RE:First_Lemma]]",
                  "* [[RE:Two]] verlinkt von [[RE:Second_Lemma]]"]
        compare(expect, task._build_entry().split("\n")[-2:])
