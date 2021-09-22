from ddt import ddt, file_data
from testfixtures import LogCapture, compare

from service.ws_re.scanner.tasks.keine_schoepfungshoehe import KSCHTask
from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.template.re_page import RePage


@ddt
class TestKSCHTask(TaskTestCase):
    @file_data("test_data/test_keine_schoepfungshoehe.yml")
    def test_process(self, text, todesjahr, keine_schoepfungshoehe, result):
        self.text_mock.return_value = text
        re_page = RePage(self.page_mock)
        with LogCapture():
            task = KSCHTask(None, self.logger)
            compare(result, task.run(re_page))
            compare(todesjahr, re_page[0]["TODESJAHR"].value)
            compare(keine_schoepfungshoehe, re_page[0]["KEINE_SCHÖPFUNGSHÖHE"].value)
