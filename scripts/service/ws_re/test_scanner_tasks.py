from scripts.service.ws_re.data_types import RePage
from datetime import datetime

import pywikibot

from scripts.service.ws_re.scanner_tasks import ReScannerTask, ERROTask, KSCHTask
from tools.bots import WikiLogger
from test import *


class TaskTestCase(TestCase):
    # todo: I don't like this, but it's working for the moment :-(, TestReScanner looks more elegant, but needs some investigation
    @mock.patch("scripts.service.ws_re.data_types.pywikibot.Page", autospec=pywikibot.Page)
    @mock.patch("scripts.service.ws_re.data_types.pywikibot.Page.text",
                new_callable=mock.PropertyMock)
    def setUp(self, text_mock, page_mock):
        self.page_mock = page_mock
        self.text_mock = text_mock
        type(self.page_mock).text = self.text_mock
        self.logger = WikiLogger(bot_name="Test", start_time=datetime(2000, 1, 1),
                                 log_to_screen=False)


class TestReScannerTask(TaskTestCase):
    class NAMETask(ReScannerTask):
        def task(self):
            pass

    class NAM1Task(ReScannerTask):
        def task(self):
            pass

    class NAMEMoreExplanationTask(ReScannerTask):
        def task(self):
            pass

    def test_name(self):
        bot = self.NAMETask(None, WikiLogger(bot_name="Test", start_time=datetime(2000, 1, 1), log_to_screen=False))
        self.assertEqual("NAME", bot.get_name())
        bot = self.NAMEMoreExplanationTask(None, WikiLogger(bot_name="Test", start_time=datetime(2000, 1, 1), log_to_screen=False))
        self.assertEqual("NAME", bot.get_name())
        bot = self.NAM1Task(None, WikiLogger(bot_name="Test", start_time=datetime(2000, 1, 1), log_to_screen=False))
        self.assertEqual("NAM1", bot.get_name())

    class MINITask(ReScannerTask):
        def task(self):
            return True

    def test_init_and_delete(self):
        with LogCapture() as log_catcher:
            task = self.MINITask(None, self.logger)
            log_catcher.check(("Test", "INFO", 'opening task MINI'))
            log_catcher.clear()
            task.finish_task()
            log_catcher.check(("Test", "INFO", "closing task MINI"))

    def test_process_task(self):
        self.text_mock.return_value = "{{REDaten}}\ntext\n{{REAutor|Autor.}}"
        re_page = RePage(self.page_mock)
        with self.MINITask(None, self.logger) as task:
            result = task.run(re_page)
        self.assertTrue(result["success"])
        self.assertFalse(result["changed"])

    class MINIAlterTask(ReScannerTask):
        def task(self):
            self.re_page[0].text = "text2"

    def test_process_task_alter_text(self):
        self.text_mock.return_value = "{{REDaten}}\ntext\n{{REAutor|Autor.}}"
        re_page = RePage(self.page_mock)
        with self.MINIAlterTask(None, self.logger) as task:
            result = task.run(re_page)
        self.assertTrue(result["success"])
        self.assertTrue(result["changed"])

    class EXCETask(ReScannerTask):
        def task(self):
            raise Exception("Buuuh")

    def test_execute_with_exception(self):
        self.text_mock.return_value = "{{REDaten}}\ntext\n{{REAutor|Autor.}}"
        re_page = RePage(self.page_mock)
        with LogCapture() as log_catcher:
            with self.EXCETask(None, self.logger) as task:
                result = task.run(re_page)
            log_catcher.check(("Test", "INFO", 'opening task EXCE'),
                              ("Test", "ERROR", 'Logging a caught exception'))
        self.assertFalse(result["success"])
        self.assertFalse(result["changed"])

    class EXCEAlteredTask(ReScannerTask):
        def task(self):
            self.re_page[0].text = "text2"
            raise Exception("Buuuh")

    def test_execute_with_exception_altered(self):
        self.text_mock.return_value = "{{REDaten}}\ntext\n{{REAutor|Autor.}}"
        re_page = RePage(self.page_mock)
        with LogCapture():
            with self.EXCEAlteredTask(None, self.logger) as task:
                result = task.run(re_page)
        self.assertFalse(result["success"])
        self.assertTrue(result["changed"])

    def test_register_processed_title(self):
        self.page_mock.title.return_value = "RE:Page"
        self.text_mock.return_value = "{{REDaten}}\ntext\n{{REAutor|Autor.}}"
        re_page = RePage(self.page_mock)
        with LogCapture():
            # page successful processed
            with self.MINITask(None, self.logger) as task:
                self.assertEqual([], task.processed_pages)
                task.run(re_page)
            self.assertEqual(["RE:Page"], task.processed_pages)
            # page not complete processed
            with self.EXCETask(None, self.logger) as task:
                self.assertEqual([], task.processed_pages)
                task.run(re_page)
            self.assertEqual([], task.processed_pages)

    class ALNAAltereNotAllTask(ReScannerTask):
        def task(self):
            self.re_page[0].text = self.re_page[0].text.replace("text", "other stuff")

    def test_process_two_tasks_alter_one(self):
        self.text_mock.return_value = "{{REDaten}}\ntext\n{{REAutor|Autor.}}"
        re_page1 = RePage(self.page_mock)
        self.text_mock.return_value = "{{REDaten}}\nother stuff\n{{REAutor|Autor.}}"
        re_page2 = RePage(self.page_mock)
        with LogCapture():
            with self.ALNAAltereNotAllTask(None, self.logger) as task:
                compare({"success": True, "changed": True}, task.run(re_page1))
                compare({"success": True, "changed": False}, task.run(re_page2))


class TestERROTask(TestCase):
    def setUp(self):
        self.logger = WikiLogger(bot_name="Test", start_time=datetime(2000, 1, 1),
                                 log_to_screen=False)

    def test_process(self):
        with LogCapture():
            task = ERROTask(None, self.logger)
            task.task(":RE:Lemma1", "scripts.service.ws_re.data_types.ReDatenException: "
                                    "The count of start templates doesn't match the count of end templates.")
            task.task(":RE:Lemma2", "scripts.service.ws_re.data_types.ReDatenException: "
                                    "REDaten has wrong key word. --> {'key': 'GEMEINFREI', 'value': '2024'}")
            self.assertRegex(task._build_entry(), "\n\n==\\d{4}-\\d{2}-\\d{2}==\n\n"
                                                  "\\* \\[\\[:RE:Lemma1\\]\\]\n"
                                                  "\\*\\* scripts\\.service\\.ws_re\\.data_types\\.ReDatenException: The count of start templates doesn't match the count of end templates.\n"
                                                  "\\* \\[\\[:RE:Lemma2\\]\\]\n"
                                                  "\\*\\* scripts\\.service\\.ws_re\\.data_types\\.ReDatenException: REDaten has wrong key word. --> \\{'key': 'GEMEINFREI', 'value': '2024'\\}"
                             )

    def test_finish_up(self):
        with patch("scripts.service.ws_re.scanner_tasks.Page", autospec=pywikibot.Page) as page_mock:
            with patch("scripts.service.ws_re.scanner_tasks.Page.text", new_callable=mock.PropertyMock(return_value="bla")) as text_mock:
                type(page_mock).text = text_mock
                with LogCapture():
                    task = ERROTask(None, self.logger, debug=False)
                    task.task(":RE:Lemma1", "scripts.service.ws_re.data_types.ReDatenException: "
                                            "The count of start templates doesn't match the count of end templates.")
                    task.finish_task()
                    self.assertEqual(1, page_mock.call_count)

    def test_finish_up_no_errors(self):
        with patch("scripts.service.ws_re.scanner_tasks.Page", autospec=pywikibot.Page) as page_mock:
            with patch("scripts.service.ws_re.scanner_tasks.Page.text", new_callable=mock.PropertyMock(return_value="bla")) as text_mock:
                type(page_mock).text = text_mock
                with LogCapture():
                    task = ERROTask(None, self.logger, debug=False)
                    task.finish_task()
                    self.assertEqual(0, page_mock.call_count)


class TestKSCHTask(TaskTestCase):
    def test_process(self):
        self.text_mock.return_value = """pre_text{{REDaten
}}
{{RE keine Schöpfungshöhe|1950}}
text
{{REAutor|Autor.}}
more text"""
        re_page = RePage(self.page_mock)
        with LogCapture():
            task = KSCHTask(None, self.logger)
            compare({'success': True, 'changed': True}, task.run(re_page))
            compare("1950", re_page[1]["TODESJAHR"].value)
            compare(True, re_page[1]["KEINE_SCHÖPFUNGSHÖHE"].value)
            compare("text", re_page[1].text)

    def test_process_varing_template(self):
        self.text_mock.return_value = """{{REDaten
}}
{{RE keine Schöpfungshöhe|tada}}
text
{{REAutor|Autor.}}"""
        re_page = RePage(self.page_mock)
        with LogCapture():
            task = KSCHTask(None, self.logger)
            compare({'success': True, 'changed': False}, task.run(re_page))
            compare("", re_page[0]["TODESJAHR"].value)
            compare(False, re_page[0]["KEINE_SCHÖPFUNGSHÖHE"].value)
            compare("{{RE keine Schöpfungshöhe|tada}}\ntext", re_page[0].text)
