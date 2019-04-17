import importlib
import inspect
from datetime import datetime
from pathlib import Path
from unittest import TestCase, mock

import pywikibot
from git import Repo
from testfixtures import LogCapture, compare, StringComparison

from scripts.service.ws_re.data_types import RePage, _REGISTER_PATH
from scripts.service.ws_re.register import Authors, VolumeRegister
from scripts.service.ws_re.scanner_tasks import ReScannerTask, ERROTask, KSCHTask, VERWTask, \
    SCANTask, TJGJTask
from scripts.service.ws_re.test_register import clear_tst_path, copy_tst_data, _TEST_REGISTER_PATH
from tools.bots import WikiLogger


class TaskTestCase(TestCase):
    # Todo: I don't like this, but it's working for the moment :-(, TestReScanner looks more elegant, but needs some investigation
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
        self.assertEqual("NAME", bot.name)
        bot = self.NAMEMoreExplanationTask(None, WikiLogger(bot_name="Test", start_time=datetime(2000, 1, 1), log_to_screen=False))
        self.assertEqual("NAME", bot.name)
        bot = self.NAM1Task(None, WikiLogger(bot_name="Test", start_time=datetime(2000, 1, 1), log_to_screen=False))
        self.assertEqual("NAM1", bot.name)

    class MINITask(ReScannerTask):
        def task(self):
            return True

    def test_init_and_delete(self):
        with LogCapture() as log_catcher:
            task = self.MINITask(None, self.logger)
            log_catcher.check(("Test", "INFO", "opening task MINI"))
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
            log_catcher.check(("Test", "INFO", "opening task EXCE"),
                              ("Test", "ERROR", "Logging a caught exception"))
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

    def test_no_dublicate_names(self):
        scanner_task_module = importlib.import_module("scripts.service.ws_re.scanner_tasks")
        attributes = tuple(a for a in dir(scanner_task_module) if not a.startswith("__"))
        task_names = list()
        for attribute in attributes:
            module_attr = getattr(scanner_task_module, attribute)
            if inspect.isclass(module_attr):
                if "ReScannerTask" in str(module_attr.__bases__):
                    task_names.append(attribute[0:4])
        # every 4 letter start of a ScannerTask class must be unique
        compare(len(task_names), len(set(task_names)))


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
        with mock.patch("scripts.service.ws_re.scanner_tasks.Page", autospec=pywikibot.Page) as page_mock:
            with mock.patch("scripts.service.ws_re.scanner_tasks.Page.text", new_callable=mock.PropertyMock(return_value="bla")) as text_mock:
                type(page_mock).text = text_mock
                with LogCapture():
                    task = ERROTask(None, self.logger, debug=False)
                    task.task(":RE:Lemma1", "scripts.service.ws_re.data_types.ReDatenException: "
                                            "The count of start templates doesn't match the count of end templates.")
                    task.finish_task()
                    self.assertEqual(1, page_mock.call_count)

    def test_finish_up_no_errors(self):
        with mock.patch("scripts.service.ws_re.scanner_tasks.Page", autospec=pywikibot.Page) as page_mock:
            with mock.patch("scripts.service.ws_re.scanner_tasks.Page.text", new_callable=mock.PropertyMock(return_value="bla")) as text_mock:
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
            compare({"success": True, "changed": True}, task.run(re_page))
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
            compare({"success": True, "changed": False}, task.run(re_page))
            compare("", re_page[0]["TODESJAHR"].value)
            compare(False, re_page[0]["KEINE_SCHÖPFUNGSHÖHE"].value)
            compare("{{RE keine Schöpfungshöhe|tada}}\ntext", re_page[0].text)


class TestVERWTask(TaskTestCase):
    def test_process(self):
        self.text_mock.return_value = """pre
{{REDaten
}}
[[Kategorie:RE:Verweisung|Lemma]]
text.
{{REAutor|OFF}}
post"""
        re_page = RePage(self.page_mock)
        with LogCapture():
            task = VERWTask(None, self.logger)
            compare({"success": True, "changed": True}, task.run(re_page))
            compare(True, re_page[1]["VERWEIS"].value)
            compare("text.", re_page[1].text)

    def test_no_sort(self):
        self.text_mock.return_value = """pre
{{REDaten
}}
[[Kategorie:RE:Verweisung]]
text.
[[Kategorie:RE:Verweisung]]lala
{{REAutor|OFF}}
post"""
        re_page = RePage(self.page_mock)
        with LogCapture():
            task = VERWTask(None, self.logger)
            compare({"success": True, "changed": True}, task.run(re_page))
            compare(True, re_page[1]["VERWEIS"].value)
            compare("text.\nlala", re_page[1].text)

    def test_no_replace_if_no_clear_connection(self):
        self.text_mock.return_value = """[[Kategorie:RE:Verweisung]]
{{REDaten
}}
text.
{{REAutor|OFF}}
[[Kategorie:RE:Verweisung]]lala"""
        re_page = RePage(self.page_mock)
        with LogCapture():
            task = VERWTask(None, self.logger)
            compare({"success": True, "changed": False}, task.run(re_page))
            compare(False, re_page[1]["VERWEIS"].value)
            compare("text.", re_page[1].text)
            compare("[[Kategorie:RE:Verweisung]]", re_page[0])
            compare("[[Kategorie:RE:Verweisung]]lala", re_page[2])

    def test_three(self):
        self.text_mock.return_value = """{{REDaten
}}
text.
[[Kategorie:RE:Verweisung]]
{{REAutor|OFF}}
{{REDaten
}}
text.
{{REAutor|OFF}}
tada
{{REDaten
}}
text.
[[Kategorie:RE:Verweisung]]
{{REAutor|OFF}}
lala"""
        re_page = RePage(self.page_mock)
        with LogCapture():
            task = VERWTask(None, self.logger)
            compare({"success": True, "changed": True}, task.run(re_page))
            self.assertTrue(re_page[0]["VERWEIS"].value)
            self.assertTrue(re_page[3]["VERWEIS"].value)
            compare("text.", re_page[0].text)
            compare("text.", re_page[1].text)
            compare("text.", re_page[3].text)

    def test_verweis_next(self):
        self.text_mock.return_value = """{{REDaten
}}
text.
[[Kategorie:RE:Verweisung]]
{{REAutor|OFF}}

{{REDaten
}}
text.
{{REAutor|OFF}}

[[Kategorie:RE:Verweisung]]

{{REDaten
}}
text.
[[Kategorie:RE:Verweisung]]
{{REAutor|OFF}}

{{REDaten
}}
text.
{{REAutor|OFF}}

[[Kategorie:RE:Verweisung]] tada"""
        re_page = RePage(self.page_mock)
        with LogCapture():
            task = VERWTask(None, self.logger)
            compare({"success": True, "changed": True}, task.run(re_page))
            for i in range(4):
                compare("text.", re_page[i].text)
            self.assertTrue(re_page[0]["VERWEIS"].value)
            self.assertTrue(re_page[1]["VERWEIS"].value)
            self.assertTrue(re_page[2]["VERWEIS"].value)
            self.assertFalse(re_page[3]["VERWEIS"].value)
            compare(5, len(re_page))


class TaskTestWithRegister(TaskTestCase):
    @classmethod
    def setUpClass(cls):
        clear_tst_path()
        Authors._REGISTER_PATH = _TEST_REGISTER_PATH
        VolumeRegister._REGISTER_PATH = _TEST_REGISTER_PATH

    @classmethod
    def tearDownClass(cls):
        Authors._REGISTER_PATH = _REGISTER_PATH
        VolumeRegister._REGISTER_PATH = _REGISTER_PATH
        clear_tst_path(renew_path=False)


class TestTJGJTask(TaskTestWithRegister):
    def setUp(self):
        super().setUp()
        copy_tst_data("authors_mapping", "authors_mapping")
        copy_tst_data("I_1_base", "I_1")
        copy_tst_data("authors_birth_3333", "authors")
        self.task = TJGJTask(None, self.logger)

    def test_move_tj_3333(self):
        self.text_mock.return_value = """{{REDaten
|TJ=3333
}}
text.
{{REAutor|Abbott}}"""
        re_page = RePage(self.page_mock)
        compare({"success": True, "changed": True}, self.task.run(re_page))
        compare("", re_page[0]["TODESJAHR"].value)
        compare("1900", re_page[0]["GEBURTSJAHR"].value)

    def test_no_birth_date(self):
        self.text_mock.return_value = """{{REDaten
|TJ=3333
}}
text.
{{REAutor|Abel}}"""
        re_page = RePage(self.page_mock)
        compare({"success": True, "changed": False}, self.task.run(re_page))
        compare("3333", re_page[0]["TODESJAHR"].value)
        compare("", re_page[0]["GEBURTSJAHR"].value)

    def test_no_author(self):
        self.text_mock.return_value = """{{REDaten
|TJ=3333
}}
text.
{{REAutor|Rumpelstilzchen}}"""
        re_page = RePage(self.page_mock)
        with LogCapture():
            compare({"success": True, "changed": False}, self.task.run(re_page))
            compare("3333", re_page[0]["TODESJAHR"].value)
            compare("", re_page[0]["GEBURTSJAHR"].value)


class TestSCANTask(TaskTestWithRegister):
    def setUp(self):
        super().setUp()
        copy_tst_data("I_1_base", "I_1")
        copy_tst_data("authors", "authors")
        copy_tst_data("authors_mapping", "authors_mapping")
        self.task = SCANTask(None, self.logger)

    def test_pushing_nothing_to_push(self):
        with mock.patch("scripts.service.ws_re.scanner_tasks.Repo", mock.Mock(spec=Repo)) as repo_mock:
            repo_mock().index.diff.return_value = []
            self.task._push_changes()
            compare(3, len(repo_mock.mock_calls))
            compare(mock.call(search_parent_directories=True), repo_mock.mock_calls[1])
            compare("().index.diff", repo_mock.mock_calls[2][0])

    def test_pushing_changes(self):
        with LogCapture():
            with mock.patch("scripts.service.ws_re.scanner_tasks.Repo", mock.Mock(spec=Repo)) as repo_mock:
                repo_mock().index.diff.return_value = ["Something has changed"]
                self.task._push_changes()
                compare(8, len(repo_mock.mock_calls))
                compare(mock.call(search_parent_directories=True), repo_mock.mock_calls[1])
                compare("().index.diff", repo_mock.mock_calls[2][0])
                compare("().git.checkout", repo_mock.mock_calls[3][0])
                compare("-b", repo_mock.mock_calls[3][1][0])
                compare(StringComparison(r"\d{6}_\d{6}_updating_registers"), repo_mock.mock_calls[3][1][1])
                compare("().git.add", repo_mock.mock_calls[4][0])
                compare(str(Path(__file__).parent.joinpath("register")), repo_mock.mock_calls[4][1][0])
                compare("().index.commit", repo_mock.mock_calls[5][0])
                compare(StringComparison(r"Updating the register at \d{6}_\d{6}"), repo_mock.mock_calls[5][1][0])
                compare("().git.push", repo_mock.mock_calls[6][0])
                compare("().git.checkout", repo_mock.mock_calls[7][0])

    def test_fetch_wikipedia_link(self):
        self.text_mock.return_value = """[[Kategorie:RE:Verweisung]]
{{REDaten
}}
text.
{{REAutor|OFF}}
[[Kategorie:RE:Verweisung]]lala"""
        re_page = RePage(self.page_mock)
        with LogCapture():
            task = SCANTask(None, self.logger)
            register = task.registers.volumes["I,1"]
