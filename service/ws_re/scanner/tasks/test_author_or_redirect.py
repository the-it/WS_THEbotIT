# pylint: disable=protected-access

from testfixtures import compare, LogCapture

from service.ws_re.scanner.tasks.author_or_redirect import REAUTask
from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.template.re_page import RePage

BASE_TASK_PYWIKIBOT_PAGE = "service.ws_re.scanner.tasks.base_task.pywikibot.Page"


class TestREAUTask(TaskTestCase):
    def test_add_cat(self):
        self.text_mock.return_value = """{{REDaten
|VERWEIS=OFF
}}
test
{{REAutor|OFF}}"""
        re_page = RePage(self.page_mock)
        with LogCapture():
            task = REAUTask(None, self.logger)
            compare({'success': True, 'changed': True}, task.run(re_page))
            self.assertTrue("[[Kategorie:RE:Weder Autor noch Verweis]]" in str(re_page))

    def test_no_cat_if_nachtrag(self):
        self.text_mock.return_value = """{{REDaten
|VERWEIS=OFF
|NACHTRAG=ON
}}
test
{{REAutor|OFF}}"""
        re_page = RePage(self.page_mock)
        with LogCapture():
            task = REAUTask(None, self.logger)
            compare({'success': True, 'changed': False}, task.run(re_page))
            self.assertFalse("[[Kategorie:RE:Weder Autor noch Verweis]]" in str(re_page))

    def test_remove_cat(self):
        self.text_mock.return_value = """{{REDaten
|VERWEIS=OFF
}}
test
{{REAutor|Tada.}}
[[Kategorie:RE:Weder Autor noch Verweis]]"""
        re_page = RePage(self.page_mock)
        with LogCapture():
            task = REAUTask(None, self.logger)
            compare({'success': True, 'changed': True}, task.run(re_page))
            self.assertFalse("[[Kategorie:RE:Weder Autor noch Verweis]]" in str(re_page))
