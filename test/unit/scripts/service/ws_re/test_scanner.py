from datetime import datetime

import pywikibot

from scripts.service.ws_re.scanner import ReScannerTask
from tools.bots import WikiLogger
from scripts.service.ws_re.data_types import RePage
from test import *


class TestReScannerTask(TestCase):
    @mock.patch("scripts.service.ws_re.data_types.pywikibot.Page", autospec=pywikibot.Page)
    @mock.patch("scripts.service.ws_re.data_types.pywikibot.Page.text", new_callable=mock.PropertyMock)
    def setUp(self, text_mock, page_mock):
        self.page_mock = page_mock
        self.text_mock = text_mock
        type(self.page_mock).text = self.text_mock
        self.logger = WikiLogger(bot_name="Test", start_time=datetime(2000, 1, 1), silence=True)

    class NAMETask(ReScannerTask):
        def task(self):
            pass

    class NAMEMoreExplanationTask(ReScannerTask):
        def task(self):
            pass

    def test_name(self):
        bot = self.NAMETask(None, WikiLogger(bot_name="Test", start_time=datetime(2000, 1, 1), silence=True))
        self.assertEqual("NAME", bot.get_name())
        bot = self.NAMEMoreExplanationTask(None, WikiLogger(bot_name="Test", start_time=datetime(2000, 1, 1), silence=True))
        self.assertEqual("NAME", bot.get_name())

    class MINITask(ReScannerTask):
        def task(self):
            return True

    def test_init_and_delete(self):
        with LogCapture() as log_catcher:
            task = self.MINITask(None, self.logger)
            log_catcher.check(("Test", "INFO", 'opening task MINI'))
            log_catcher.clear()
            del task
            log_catcher.check(("Test", "INFO", "closing task MINI"))

    def test_process_task(self):
        self.text_mock.return_value = "{{REDaten}}\ntext\n{{REAutor|Autor.}}"
        re_page = RePage(self.page_mock)
        with self.MINITask(None, self.logger) as task:
            result = task.run(re_page)
            self.assertTrue(result["success"])
            self.assertFalse(result["changed"])

    class EXCETask(ReScannerTask):
        def task(self):
            raise Exception("Buuuh")

    def test_execute_with_exception(self):
        self.text_mock.return_value = "{{REDaten}}\ntext\n{{REAutor|Autor.}}"
        re_page = RePage(self.page_mock)
        with LogCapture() as log_catcher:
            with self.EXCETask(None, self.logger) as task:
                result = task.run(re_page)
            self.assertFalse(result["success"])
            self.assertFalse(result["changed"])
            log_catcher.check(("Test", "INFO", 'opening task EXCE'),
                              ("Test", "ERROR", 'Logging a caught exception'))

