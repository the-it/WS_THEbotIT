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
from scripts.service.ws_re.scanner_tasks import ReScannerTask, ERROTask, KSCHTask, SCANTask, DEALTask, DEWPTask
from scripts.service.ws_re.test_register import clear_tst_path, copy_tst_data, _TEST_REGISTER_PATH
from tools.bots import WikiLogger


class TaskTestCase(TestCase):
    # Todo: I don't like this, but it's working for the moment :-(, TestReScanner looks more elegant, but needs some investigation
    @mock.patch("scripts.service.ws_re.data_types.pywikibot.Page", autospec=pywikibot.Page)
    @mock.patch("scripts.service.ws_re.data_types.pywikibot.Page.text", new_callable=mock.PropertyMock)
    @mock.patch("scripts.service.ws_re.data_types.pywikibot.Page.title", new_callable=mock.Mock)
    def setUp(self, title_mock, text_mock, page_mock):
        self.page_mock = page_mock
        self.text_mock = text_mock
        self.title_mock = title_mock
        type(self.page_mock).text = self.text_mock
        type(self.page_mock).title = self.title_mock
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
        with mock.patch("scripts.service.ws_re.scanner_tasks.pywikibot.Page", autospec=pywikibot.Page) as page_mock:
            with mock.patch("scripts.service.ws_re.scanner_tasks.pywikibot.Page.text", new_callable=mock.PropertyMock(return_value="bla")) as text_mock:
                type(page_mock).text = text_mock
                with LogCapture():
                    task = ERROTask(None, self.logger, debug=False)
                    task.task(":RE:Lemma1", "scripts.service.ws_re.data_types.ReDatenException: "
                                            "The count of start templates doesn't match the count of end templates.")
                    task.finish_task()
                    self.assertEqual(1, page_mock.call_count)

    def test_finish_up_no_errors(self):
        with mock.patch("scripts.service.ws_re.scanner_tasks.pywikibot.Page", autospec=pywikibot.Page) as page_mock:
            with mock.patch("scripts.service.ws_re.scanner_tasks.pywikibot.Page.text", new_callable=mock.PropertyMock(return_value="bla")) as text_mock:
                type(page_mock).text = text_mock
                with LogCapture():
                    task = ERROTask(None, self.logger, debug=False)
                    task.finish_task()
                    self.assertEqual(0, page_mock.call_count)


class TestDEALTask(TaskTestCase):
    def test_process_next_previous(self):
        with mock.patch("scripts.service.ws_re.scanner_tasks.pywikibot.Page",
                        new_callable=mock.MagicMock) as page_mock:
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
        with mock.patch("scripts.service.ws_re.scanner_tasks.pywikibot.Page",
                        new_callable=mock.MagicMock) as page_mock:
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
        with mock.patch("scripts.service.ws_re.scanner_tasks.pywikibot.Page",
                        new_callable=mock.MagicMock) as page_mock:
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
        with mock.patch("scripts.service.ws_re.scanner_tasks.pywikibot.Page",
                        new_callable=mock.MagicMock) as page_mock:
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
        with mock.patch("scripts.service.ws_re.scanner_tasks.pywikibot.Page",
                        new_callable=mock.MagicMock) as page_mock:
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
        with mock.patch("scripts.service.ws_re.scanner_tasks.pywikibot.Page",
                        new_callable=mock.MagicMock) as page_mock:
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
        with mock.patch("scripts.service.ws_re.scanner_tasks.pywikibot.Page",
                        new_callable=mock.MagicMock) as page_mock:
            with open(Path(__file__).parent.joinpath("test_data_scanner/bug_value_error_DEAL_task.txt"), encoding="utf-8") as bug_file:
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


class TestDEWPTask(TaskTestCase):
    def test_link_is_missing(self):
        with mock.patch("scripts.service.ws_re.scanner_tasks.pywikibot.Page",
                        new_callable=mock.MagicMock) as page_mock:
            self.text_mock.return_value = """{{REDaten
|WP=Bla
}}
{{REAutor|Autor.}}"""
            self.title_mock.return_value = "Re:Title"
            page_mock.return_value.exists.side_effect = [False]
            re_page = RePage(self.page_mock)
            task = DEWPTask(None, self.logger)
            compare({"success": True, "changed": False}, task.run(re_page))
            compare([("Bla", "Title")], task.data)

    def test_link_is_existend(self):
        with mock.patch("scripts.service.ws_re.scanner_tasks.pywikibot.Page",
                        new_callable=mock.MagicMock) as page_mock:
            self.text_mock.return_value = """{{REDaten
|WP=Bla
}}
{{REAutor|Autor.}}"""
            self.title_mock.return_value = "Re:Title"
            page_mock.return_value.exists.side_effect = [True]
            re_page = RePage(self.page_mock)
            task = DEWPTask(None, self.logger)
            compare({"success": True, "changed": False}, task.run(re_page))
            compare([], task.data)

    def test_link_several_links(self):
        with mock.patch("scripts.service.ws_re.scanner_tasks.pywikibot.Page",
                        new_callable=mock.MagicMock) as page_mock:
            self.text_mock.return_value = """{{REDaten|WP=Bla}}
{{REAutor|Autor.}}
{{REDaten|WP=Blub}}
{{REAutor|Autor.}}
{{REDaten}}
{{REAutor|Autor.}}
{{REDaten|WP=Blab}}
{{REAutor|Autor.}}"""
            self.title_mock.return_value = "Re:Title"
            page_mock.return_value.exists.side_effect = [True, False, False]
            re_page = RePage(self.page_mock)
            task = DEWPTask(None, self.logger)
            compare({"success": True, "changed": False}, task.run(re_page))
            compare([("Blub", "Title"), ("Blab", "Title")], task.data)

            self.text_mock.return_value = """{{REDaten|WP=Bli}}
{{REAutor|Autor.}}"""
            self.title_mock.return_value = "Re:Title2"
            page_mock.return_value.exists.side_effect = [False]
            re_page = RePage(self.page_mock)
            compare({"success": True, "changed": False}, task.run(re_page))
            compare([("Blub", "Title"), ("Blab", "Title"), ("Bli", "Title2")], task.data)

    def test_build_entries(self):
        task = DEWPTask(None, self.logger)
        task.data = [("One", "First_Lemma"), ("Two", "Second_Lemma")]
        expect = ["* Wikpedia Artikel: [[wp:One]] verlinkt von [[RE:First_Lemma]] existiert nicht",
                  "* Wikpedia Artikel: [[wp:Two]] verlinkt von [[RE:Second_Lemma]] existiert nicht"]
        compare(expect, task._build_entry().split("\n")[-2:])


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

    def test_fetch_wikipedia_wikisource_link(self):
        self.text_mock.return_value = """{{REDaten
|BAND=I,1
|WP=Lemma
|WS=WsLemma
}}
text.
{{REAutor|OFF}}"""
        article = RePage(self.page_mock).splitted_article_list[0]
        compare(({"wp_link": "w:de:Lemma"}, []), SCANTask._fetch_wp_link(article))
        compare(({"ws_link": "s:de:WsLemma"}, []), SCANTask._fetch_ws_link(article))

    def test_fetch_wikipedia_link_no_link(self):
        self.text_mock.return_value = """{{REDaten
|BAND=I,1
}}
text.
{{REAutor|OFF}}"""
        article = RePage(self.page_mock).splitted_article_list[0]
        compare(({}, ["wp_link"]), SCANTask._fetch_wp_link(article))
        compare(({}, ["ws_link"]), SCANTask._fetch_ws_link(article))

    def test_sortkey(self):
        self.text_mock.return_value = """{{REDaten
|BAND=I,1
|SORTIERUNG=Abalas limen
}}
text.
{{REAutor|OFF}}"""
        article = RePage(self.page_mock).splitted_article_list[0]
        compare(({"sort_key": "Abalas limen"}, []), SCANTask._fetch_sort_key(article))

        self.text_mock.return_value = """{{REDaten
|BAND=I,1
}}
text.
{{REAutor|OFF}}"""
        article = RePage(self.page_mock).splitted_article_list[0]
        compare(({}, ["sort_key"]), SCANTask._fetch_sort_key(article))

    def test_lemma(self):
        self.title_mock.return_value = "RE:Aal"
        self.text_mock.return_value = """{{REDaten
|BAND=I,1
}}
text.
{{REAutor|OFF}}"""
        re_page = RePage(self.page_mock)
        article = re_page.splitted_article_list[0]
        task = SCANTask(None, self.logger)
        task.re_page =  re_page
        compare(({"lemma": "Aal"}, []), task._fetch_lemma(article))

    def test_redirect(self):
        self.text_mock.return_value = """{{REDaten
|BAND=I,1
|VERWEIS=ON
}}
text.
{{REAutor|OFF}}"""
        article = RePage(self.page_mock).splitted_article_list[0]
        compare(({"redirect": True}, []), SCANTask._fetch_redirect(article))

        self.text_mock.return_value = """{{REDaten
|BAND=I,1
|VERWEIS=OFF
}}
text.
{{REAutor|OFF}}"""
        article = RePage(self.page_mock).splitted_article_list[0]
        compare(({}, ["redirect"]), SCANTask._fetch_redirect(article))

    def test_previous(self):
        self.text_mock.return_value = """{{REDaten
|BAND=I,1
|VG=Lemma Previous
}}
text.
{{REAutor|OFF}}"""
        article = RePage(self.page_mock).splitted_article_list[0]
        compare(({"previous": "Lemma Previous"}, []), SCANTask._fetch_previous(article))
        self.text_mock.return_value = """{{REDaten
|BAND=I,1
|VG=OFF
}}
text.
{{REAutor|OFF}}"""
        article = RePage(self.page_mock).splitted_article_list[0]
        compare(({}, ["previous"]), SCANTask._fetch_previous(article))
        self.text_mock.return_value = """{{REDaten
|BAND=I,1
}}
text.
{{REAutor|OFF}}"""
        article = RePage(self.page_mock).splitted_article_list[0]
        compare(({}, ["previous"]), SCANTask._fetch_previous(article))

    def test_next(self):
        self.text_mock.return_value = """{{REDaten
|BAND=I,1
|NF=Lemma Next
}}
text.
{{REAutor|OFF}}"""
        article = RePage(self.page_mock).splitted_article_list[0]
        compare(({"next": "Lemma Next"}, []), SCANTask._fetch_next(article))
        self.text_mock.return_value = """{{REDaten
|BAND=I,1
|NF=OFF
}}
text.
{{REAutor|OFF}}"""
        article = RePage(self.page_mock).splitted_article_list[0]
        compare(({}, ["next"]), SCANTask._fetch_next(article))
        self.text_mock.return_value = """{{REDaten
|BAND=I,1
}}
text.
{{REAutor|OFF}}"""
        article = RePage(self.page_mock).splitted_article_list[0]
        compare(({}, ["next"]), SCANTask._fetch_next(article))

    def test_fetch_from_properties(self):
        self.title_mock.return_value = "RE:Aal"
        self.text_mock.return_value = """{{REDaten
|BAND=I,1
|VORGÄNGER=Lemma Previous
|NACHFOLGER=Lemma Next
|WP=Aal_wp_link
|WS=Aal_ws_link
|SORTIERUNG=Aal
|VERWEIS=ON
}}
text.
{{REAutor|OFF}}"""
        task = SCANTask(None, self.logger)
        task.re_page = RePage(self.page_mock)
        task._fetch_from_article_list()
        post_lemma = task.registers["I,1"].get_lemma_by_name("Aal")
        compare("w:de:Aal_wp_link", post_lemma.lemma_dict["wp_link"])
        compare("s:de:Aal_ws_link", post_lemma.lemma_dict["ws_link"])
        compare("Aal", post_lemma.lemma_dict["sort_key"])
        compare(True, post_lemma.lemma_dict["redirect"])
        print("workaround")
        # compare("Lemma Previous", post_lemma.lemma_dict["previous"])
        # compare("Lemma Next", post_lemma.lemma_dict["next"])

    def test_fetch_from_properties_lemma_not_found(self):
        self.title_mock.return_value = "RE:Aas"
        self.text_mock.return_value = """{{REDaten
|BAND=I,1
|WP=Aal_wp_link
|WS=Aal_ws_link
}}
text.
{{REAutor|OFF}}"""
        task = SCANTask(None, self.logger)
        task.re_page = RePage(self.page_mock)
        with LogCapture() as log_catcher:
            task._fetch_from_article_list()
            log_catcher.check(("Test", "ERROR", StringComparison("No available Lemma in Registers for issue I,1 .* Reason is:.*")))
