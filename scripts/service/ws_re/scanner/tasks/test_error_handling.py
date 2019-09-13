from datetime import datetime
from unittest import TestCase, mock

import pywikibot
from testfixtures import LogCapture

from scripts.service.ws_re.scanner import ERROTask
from tools.bots import WikiLogger


class TestERROTask(TestCase):
    def setUp(self):
        self.logger = WikiLogger(bot_name="Test", start_time=datetime(2000, 1, 1),
                                 log_to_screen=False)

    def test_process(self):
        with LogCapture():
            task = ERROTask(None, self.logger)
            task.append_error(":RE:Lemma1", "scripts.service.ws_re.template.ReDatenException: "
                                            "The count of start templates doesn't match the count of end templates.")
            task.append_error(":RE:Lemma2", "scripts.service.ws_re.template.ReDatenException: "
                                            "REDaten has wrong key word. --> {'key': 'GEMEINFREI', 'value': '2024'}")
            self.assertRegex(task._build_entry(), "\n\n==\\d{4}-\\d{2}-\\d{2}==\n\n"
                                                  "\\* \\[\\[:RE:Lemma1\\]\\]\n"
                                                  "\\*\\* scripts\\.service\\.ws_re\\.template\\.ReDatenException: The count of start templates doesn't match the count of end templates.\n"
                                                  "\\* \\[\\[:RE:Lemma2\\]\\]\n"
                                                  "\\*\\* scripts\\.service\\.ws_re\\.template\\.ReDatenException: REDaten has wrong key word. --> \\{'key': 'GEMEINFREI', 'value': '2024'\\}"
                             )

    def test_finish_up(self):
        with mock.patch("scripts.service.ws_re.scanner.tasks.base_task.pywikibot.Page", autospec=pywikibot.Page) as page_mock:
            with mock.patch("scripts.service.ws_re.scanner.tasks.base_task.pywikibot.Page.text", new_callable=mock.PropertyMock(return_value="bla")) as text_mock:
                type(page_mock).text = text_mock
                with LogCapture():
                    task = ERROTask(None, self.logger, debug=False)
                    task.append_error(":RE:Lemma1", "scripts.service.ws_re.template.ReDatenException: "
                                                    "The count of start templates doesn't match the count of end templates.")
                    task.finish_task()
                    self.assertEqual(1, page_mock.call_count)

    def test_finish_up_no_errors(self):
        with mock.patch("scripts.service.ws_re.scanner.tasks.base_task.pywikibot.Page", autospec=pywikibot.Page) as page_mock:
            with mock.patch("scripts.service.ws_re.scanner.tasks.base_task.pywikibot.Page.text", new_callable=mock.PropertyMock(return_value="bla")) as text_mock:
                type(page_mock).text = text_mock
                with LogCapture():
                    task = ERROTask(None, self.logger, debug=False)
                    task.finish_task()
                    self.assertEqual(0, page_mock.call_count)
