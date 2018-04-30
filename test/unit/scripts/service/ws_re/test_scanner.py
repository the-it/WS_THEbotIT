from datetime import datetime

import pywikibot

from scripts.service.ws_re.scanner import ReScannerTask, ReScanner
from tools.bots import WikiLogger
from tools.catscan import PetScan
from scripts.service.ws_re.data_types import RePage
from test import *
from test.unit.tools.test_bots import setup_data_path, teardown_data_path


class TestReScannerTask(TestCase):
    # todo: I don't like this, but it's working for the moment :-(, TestReScanner looks more elegant, but needs some investigation
    @mock.patch("scripts.service.ws_re.data_types.pywikibot.Page", autospec=pywikibot.Page)
    @mock.patch("scripts.service.ws_re.data_types.pywikibot.Page.text", new_callable=mock.PropertyMock)
    def setUp(self, text_mock, page_mock):
        self.page_mock = page_mock
        self.text_mock = text_mock
        type(self.page_mock).text = self.text_mock
        self.logger = WikiLogger(bot_name="Test", start_time=datetime(2000, 1, 1), log_to_screen=False)

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
            del task
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


class TestReScanner(TestCase):
    def setUp(self):
        self.petscan_patcher = patch("scripts.service.ws_re.scanner.PetScan", autospec=PetScan)
        self.petscan_mock = self.petscan_patcher.start()
        self.run_mock = mock.Mock()
        self.petscan_mock.return_value = mock.Mock(run=self.run_mock)
        setup_data_path(self)
        self.addCleanup(patch.stopall)
        self.log_patcher = patch.object(WikiLogger, 'debug', autospec=True)
        self.wiki_logger_mock = self.log_patcher.start()

    def tearDown(self):
        teardown_data_path()
        mock.patch.stopall()

    class SearchStringChecker(object):
        def __init__(self, search_string: str):
            self.search_string = search_string

        def is_part_of_searchstring(self, part: str):
            pre_length = len(self.search_string)
            self.search_string = "".join(self.search_string.split(part))
            return pre_length != len(self.search_string)

        def is_empty(self):
            return len(self.search_string) == 0

    def test_search_prepare_debug(self):
        mock.patch.stopall()
        with ReScanner(log_to_screen=False, log_to_wiki=False) as bot:
            checker = self.SearchStringChecker(str(bot._prepare_searcher()))
            self.assertTrue(checker.is_part_of_searchstring(
                r"https://petscan.wmflabs.org/?language=de&project=wikisource"))
            self.assertTrue(checker.is_part_of_searchstring("&templates_any=REDaten"))
            self.assertTrue(checker.is_part_of_searchstring("&ns%5B2%5D=1"))
            self.assertTrue(checker.is_empty())

    def test_search_prepare(self):
        mock.patch.stopall()
        with ReScanner(log_to_screen=False, log_to_wiki=False, debug=False) as bot:
            checker = self.SearchStringChecker(str(bot._prepare_searcher()))
            self.assertTrue(checker.is_part_of_searchstring(
                "https://petscan.wmflabs.org/?language=de&project=wikisource"))
            self.assertTrue(checker.is_part_of_searchstring(
                "&categories=Fertig%2BRE%0D%0AKorrigiert%2BRE%0D%0ARE:Platzhalter"))
            self.assertTrue(checker.is_part_of_searchstring("&templates_any=REDaten"))
            self.assertTrue(checker.is_part_of_searchstring("&ns%5B0%5D=1"))
            self.assertTrue(checker.is_part_of_searchstring("&combination=union"))
            self.assertTrue(checker.is_part_of_searchstring("&sortby=date"))
            self.assertTrue(checker.is_part_of_searchstring("&sortorder=descending"))
            self.assertTrue(checker.is_empty())

    result_of_searcher = [{'id': 42, 'len': 42, 'n': 'page', 'namespace': 0, 'nstext': '',
                           'title': 'RE:Lemma1', 'touched': '20010101232359'},
                          {'id': 42, 'len': 42, 'n': 'page', 'namespace': 0, 'nstext': '',
                           'title': 'RE:Lemma2', 'touched': '20000101232359'},
                          {'id': 42, 'len': 42, 'n': 'page', 'namespace': 0, 'nstext': '',
                           'title': 'RE:Lemma3', 'touched': '19990101232359'}
                          ]

    def test_compile_lemmas_no_old_lemmas(self):

        self.run_mock.return_value = self.result_of_searcher
        with ReScanner(log_to_screen=False, log_to_wiki=False) as bot:
            self.assertEqual([':RE:Lemma1', ':RE:Lemma2', ':RE:Lemma3'], bot.compile_lemma_list())

    def test_compile_lemmas_old_lemmas(self):
        self.run_mock.return_value = self.result_of_searcher
        with ReScanner(log_to_screen=False, log_to_wiki=False) as bot:
            with mock.patch.dict(bot.data, {":RE:Lemma1": '20010101232359'}):
                self.assertEqual([':RE:Lemma2', ':RE:Lemma3', ':RE:Lemma1'], bot.compile_lemma_list())
            with mock.patch.dict(bot.data, {":RE:Lemma1": '20010101232359',
                                            ":RE:Lemma3": '20020101232359'}):
                self.assertEqual([':RE:Lemma2', ':RE:Lemma1', ':RE:Lemma3'], bot.compile_lemma_list())

    class ONE1Task(ReScannerTask):
        def task(self):
            self.logger.info("I")

    class TWO2Task(ReScannerTask):
        def task(self):
            self.logger.info("II")

    def test_activate_tasks(self):
        with ReScanner(log_to_screen=False, log_to_wiki=False) as bot:
            bot.tasks = [self.ONE1Task, self.TWO2Task]
            tasks_to_run = bot._activate_tasks()
            self.assertEqual(2, len(tasks_to_run))
            for item in tasks_to_run:
                self.assertEqual(ReScannerTask, type(item).__bases__[0])

    def _mock_surroundings(self, lemmas, ):
        self.lemma_patcher = patch("scripts.service.ws_re.scanner.ReScanner.compile_lemma_list",
                                   mock.Mock(return_value=lemmas))
        self.page_patcher = patch("scripts.service.ws_re.scanner.Page", autospec=pywikibot.Page)
        self.re_page_patcher = patch("scripts.service.ws_re.scanner.RePage", autospec=RePage)


        self.lemma_mock = self.lemma_patcher.start()

        @mock.patch("scripts.service.ws_re.data_types.pywikibot.Page", autospec=pywikibot.Page)
        @mock.patch("scripts.service.ws_re.data_types.pywikibot.Page.text",
                    new_callable=mock.PropertyMock)
        def setUp(self, text_mock, page_mock):
            type(self.page_mock).text = self.text_mock

    @ skip
    def test_one_tasks_one_lemma(self):
        self._mock_surroundings([':RE:Lemma1'])
        self.page_mock.title.return_value = "RE:Lemma1"
        self.text_mock.return_value = "{{REDaten}}\ntext\n{{REAutor|Autor.}}"
        with LogCapture() as log_catcher:
            with ReScanner(silence=False) as bot:
                log_catcher.clear()
                bot.tasks = [self.ONE1Task]
                bot.run()
                print(log_catcher)
                # log_catcher.check(("Test", "INFO", 'opening task EXCE'),
                #                   ("Test", "ERROR", 'Logging a caught exception'))
