# pylint: disable=protected-access
from contextlib import suppress
from datetime import datetime
from unittest import mock, skip

from freezegun import freeze_time
from testfixtures import LogCapture

from service.ws_re.scanner.base import ReScanner
from service.ws_re.scanner.tasks.base_task import ReScannerTask
from service.ws_re.template import ReDatenException
from tools.bots.test_base import TestCloudBase
from tools.test import SearchStringChecker


class TestReScanner(TestCloudBase):
    def setUp(self):
        self.petscan_patcher = mock.patch("service.ws_re.scanner.base.PetScan.get_combined_lemma_list")
        self.petscan_mock = self.petscan_patcher.start()
        self.addCleanup(mock.patch.stopall)

    def tearDown(self):
        mock.patch.stopall()

    def test_search_prepare_debug(self):
        mock.patch.stopall()
        with ReScanner(log_to_screen=False, log_to_wiki=False) as bot:
            checker = SearchStringChecker(str(bot._prepare_searcher()))
            self.assertTrue(checker.is_part_of_searchstring(
                r"https://petscan.wmflabs.org/?language=de&project=wikisource"))
            self.assertTrue(checker.is_part_of_searchstring("&templates_yes=REDaten"))
            self.assertTrue(checker.is_part_of_searchstring("&ns%5B2%5D=1"))
            self.assertTrue(checker.is_empty())

    def test_search_prepare(self):
        mock.patch.stopall()
        with ReScanner(log_to_screen=False, log_to_wiki=False, debug=False) as bot:
            checker = SearchStringChecker(str(bot._prepare_searcher()))
            self.assertTrue(checker.is_part_of_searchstring(
                "https://petscan.wmflabs.org/?language=de&project=wikisource"))
            self.assertTrue(checker.is_part_of_searchstring(
                "&categories=RE:Fertig%0D%0ARE:Korrigiert%0D%0ARE:Platzhalter"))
            self.assertTrue(checker.is_part_of_searchstring("&templates_yes=REDaten"))
            self.assertTrue(checker.is_part_of_searchstring("&ns%5B0%5D=1"))
            self.assertTrue(checker.is_part_of_searchstring("&combination=union"))
            self.assertTrue(checker.is_part_of_searchstring("&sortby=date"))
            self.assertTrue(checker.is_part_of_searchstring("&sortorder=descending"))
            self.assertTrue(checker.is_empty())

    def test_get_oldest_processed(self):
        with ReScanner(log_to_screen=False, log_to_wiki=False) as bot:
            with mock.patch.dict(bot.data, {":RE:Lemma1": "20010101000000",
                                            ":RE:Lemma2": "20080101232359",
                                            ":RE:Lemma3": "20020101232359"}):
                self.assertEqual(datetime(year=2001, month=1, day=1),
                                 bot.get_oldest_datetime())

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

    def _mock_surroundings(self):
        # pylint: disable=attribute-defined-outside-init
        lemma_patcher = mock.patch("service.ws_re.scanner.base.ReScanner.lemma_list",
                                   mock.PropertyMock())
        page_patcher = mock.patch("service.ws_re.scanner.base.pywikibot.Page")
        page_patcher_error = mock.patch("service.ws_re.scanner.tasks.base_task.pywikibot.Page")
        re_page_patcher = mock.patch("service.ws_re.scanner.base.RePage")
        self.lemma_mock = lemma_patcher.start()
        self.page_mock = page_patcher.start()
        self.page_error_mock = page_patcher_error.start()
        self.re_page_mock = re_page_patcher.start()

    def _mock_task(self):
        # pylint: disable=attribute-defined-outside-init
        task_patcher = mock.patch("service.ws_re.scanner.base.ReScannerTask.run")
        self.task_mock = task_patcher.start()

    def test_one_tasks_one_lemma(self):
        self._mock_surroundings()
        self.lemma_mock.return_value = [":RE:Lemma1"]
        with suppress(AssertionError):
            with LogCapture() as log_catcher:
                with ReScanner(log_to_screen=False, log_to_wiki=False, debug=False) as bot:
                    log_catcher.clear()
                    bot.tasks = [self.ONE1Task]
                    bot.run()
                    expected_logging = (("ReScanner", "INFO", "opening task ONE1"),
                                        ("ReScanner", "INFO", "opening task ERRO"),
                                        ("ReScanner", "INFO", "Start processing the lemmas."),
                                        ("ReScanner", "DEBUG",
                                         "Process [https://de.wikisource.org/wiki/:RE:Lemma1 :RE:Lemma1]"),
                                        ("ReScanner", "INFO", "I"),
                                        ("ReScanner", "DEBUG", "ReScanner hat folgende Aufgaben bearbeitet: BASE"),
                                        ("ReScanner", "INFO", "closing task ONE1"),
                                        ("ReScanner", "INFO", "closing task ERRO"))
                    log_catcher.check_present(*expected_logging, order_matters=True)

    def test_two_tasks_one_lemma(self):
        self._mock_surroundings()
        self.lemma_mock.return_value = [":RE:Lemma1"]
        with suppress(AssertionError):
            with LogCapture() as log_catcher:
                with ReScanner(log_to_screen=False, log_to_wiki=False, debug=False) as bot:
                    log_catcher.clear()
                    bot.tasks = [self.ONE1Task, self.TWO2Task]
                    bot.run()
                    expected_logging = (("ReScanner", "INFO", "opening task ONE1"),
                                        ("ReScanner", "INFO", "opening task TWO2"),
                                        ("ReScanner", "INFO", "opening task ERRO"),
                                        ("ReScanner", "INFO", "Start processing the lemmas."),
                                        ("ReScanner", "DEBUG",
                                         "Process [https://de.wikisource.org/wiki/:RE:Lemma1 :RE:Lemma1]"),
                                        ("ReScanner", "INFO", "I"),
                                        ("ReScanner", "INFO", "II"),
                                        ("ReScanner", "DEBUG", "ReScanner hat folgende Aufgaben bearbeitet: BASE"),
                                        ("ReScanner", "INFO", "closing task ONE1"),
                                        ("ReScanner", "INFO", "closing task TWO2"),
                                        ("ReScanner", "INFO", "closing task ERRO"))
                    log_catcher.check_present(*expected_logging, order_matters=True)

    def test_lemma_raise_exception(self):
        self._mock_surroundings()
        self.lemma_mock.return_value = [":RE:Lemma1"]
        self.re_page_mock.side_effect = ReDatenException
        with suppress(AssertionError):
            with LogCapture() as log_catcher:
                with ReScanner(log_to_screen=False, log_to_wiki=False) as bot:
                    log_catcher.clear()
                    bot.tasks = [self.ONE1Task]
                    bot.run()
                    expected_logging = (("ReScanner", "ERROR",
                                         "The initiation of [[:RE:Lemma1]] went wrong: "
                                         "service.ws_re.template.ReDatenException"),)
                    log_catcher.check_present(*expected_logging, order_matters=True)

    def test_lemma_raise_exception_second_not(self):
        self._mock_surroundings()
        self.lemma_mock.return_value = [":RE:Lemma1", ":RE:Lemma2"]
        self.re_page_mock.side_effect = [ReDatenException, mock.DEFAULT]
        with suppress(AssertionError):
            with LogCapture() as log_catcher:
                with ReScanner(log_to_screen=False, log_to_wiki=False) as bot:
                    log_catcher.clear()
                    bot.tasks = [self.ONE1Task]
                    bot.run()
                    expected_logging = (("ReScanner", "DEBUG",
                                         "Process [https://de.wikisource.org/wiki/:RE:Lemma1 :RE:Lemma1]"),
                                        ("ReScanner", "ERROR",
                                         "The initiation of [[:RE:Lemma1]] went wrong: "
                                         "service.ws_re.template.ReDatenException"),
                                        ("ReScanner", "DEBUG",
                                         "Process [https://de.wikisource.org/wiki/:RE:Lemma2 :RE:Lemma2]"),
                                        ("ReScanner", "INFO", "I"))
                    log_catcher.check_present(*expected_logging, order_matters=True)

    def test_re_page_return_success_nothing_changed(self):
        self._mock_surroundings()
        self._mock_task()
        self.lemma_mock.return_value = [":RE:Lemma1"]
        self.task_mock.return_value = {"success": True, "changed": False}
        with suppress(AssertionError):
            with LogCapture() as log_catcher:
                with ReScanner(log_to_screen=False, log_to_wiki=False, debug=False) as bot:
                    log_catcher.clear()
                    bot.tasks = [self.ONE1Task]
                    bot.run()
                    expected_logging = (("ReScanner", "DEBUG",
                                         "Process [https://de.wikisource.org/wiki/:RE:Lemma1 :RE:Lemma1]"),
                                        ("ReScanner", "DEBUG", "ReScanner hat folgende Aufgaben bearbeitet: BASE"))
                    log_catcher.check_present(*expected_logging, order_matters=True)

    def test_re_page_return_success_text_changed(self):
        self._mock_surroundings()
        self._mock_task()
        self.lemma_mock.return_value = [":RE:Lemma1"]
        self.task_mock.return_value = {"success": True, "changed": True}
        with suppress(AssertionError):
            with LogCapture(level=0) as log_catcher:
                with ReScanner(log_to_screen=False, log_to_wiki=False, debug=False) as bot:
                    log_catcher.clear()
                    bot.tasks = [self.ONE1Task]
                    bot.run()
                    expected_logging = (("ReScanner", "DEBUG",
                                         "Process [https://de.wikisource.org/wiki/:RE:Lemma1 :RE:Lemma1]"),
                                        ("ReScanner", "DEBUG",
                                         "ReScanner hat folgende Aufgaben bearbeitet: BASE, ONE1"))
                    log_catcher.check_present(*expected_logging, order_matters=True)

    def test_re_page_return_no_success_nothing_changed(self):
        self._mock_surroundings()
        self._mock_task()
        self.lemma_mock.return_value = [":RE:Lemma1"]
        self.task_mock.return_value = {"success": False, "changed": False}
        with suppress(AssertionError):
            with LogCapture() as log_catcher:
                with ReScanner(log_to_screen=False, log_to_wiki=False, debug=False) as bot:
                    log_catcher.clear()
                    bot.tasks = [self.ONE1Task]
                    bot.run()
                    expected_logging = (("ReScanner", "DEBUG",
                                         "Process [https://de.wikisource.org/wiki/:RE:Lemma1 :RE:Lemma1]"),
                                        ("ReScanner", "ERROR", "Error in ONE1/[[:RE:Lemma1]], no data was altered."),
                                        ("ReScanner", "DEBUG", "ReScanner hat folgende Aufgaben bearbeitet: BASE"))
                    log_catcher.check_present(*expected_logging, order_matters=True)

    def test_re_page_return_no_success_but_text_has_changed(self):
        self._mock_surroundings()
        self._mock_task()
        self.lemma_mock.return_value = [":RE:Lemma1"]
        self.task_mock.return_value = {"success": False, "changed": True}
        with suppress(AssertionError):
            with LogCapture() as log_catcher:
                with ReScanner(log_to_screen=False, log_to_wiki=False, debug=False) as bot:
                    log_catcher.clear()
                    bot.tasks = [self.ONE1Task]
                    bot.run()
                    expected_logging = (("ReScanner", "DEBUG",
                                         "Process [https://de.wikisource.org/wiki/:RE:Lemma1 :RE:Lemma1]"),
                                        ("ReScanner", "CRITICAL",
                                         "Error in ONE1/[[:RE:Lemma1]], but altered the page ... critical"))
                    log_catcher.check_present(*expected_logging, order_matters=True)

    def test_watchdog(self):
        self._mock_surroundings()
        self.lemma_mock.return_value = [":RE:Lemma1", ":RE:Lemma2"]
        with mock.patch("service.ws_re.scanner.base.ReScanner._watchdog", mock.Mock(return_value=True)):
            with suppress(AssertionError):
                with LogCapture() as log_catcher:
                    with ReScanner(log_to_screen=False, log_to_wiki=False, debug=False) as bot:
                        log_catcher.clear()
                        bot.tasks = [self.ONE1Task]
                        bot.run()
                        expected_logging = (("ReScanner", "DEBUG",
                                             "Process [https://de.wikisource.org/wiki/:RE:Lemma1 :RE:Lemma1]"),
                                            ("ReScanner", "INFO", "I"),
                                            ("ReScanner", "DEBUG", "ReScanner hat folgende Aufgaben bearbeitet: BASE"),
                                            ("ReScanner", "INFO", "closing task ONE1"))
                        log_catcher.check_present(*expected_logging, order_matters=True)

    @skip("I quit this task for the moment")
    def test_save_going_wrong(self):
        self._mock_surroundings()

        def side_effect(*args, **kwargs):
            raise ReDatenException(args, kwargs)

        save_mock = mock.patch("service.ws_re.scanner.RePage.save",
                               new_callable=mock.Mock()).start()
        type(self.re_page_mock).save = save_mock.start()
        save_mock.side_effect = side_effect
        self.lemma_mock.return_value = [":RE:Lemma1"]
        with LogCapture() as log_catcher:
            with ReScanner(log_to_screen=False, log_to_wiki=False, debug=False) as bot:
                log_catcher.clear()
                bot.tasks = [self.ONE1Task]
                bot.run()
                expected_logging = (("ReScanner", "INFO",
                                     "Process [https://de.wikisource.org/wiki/:RE:Lemma1 :RE:Lemma1]"),
                                    ("ReScanner", "INFO", "I"),
                                    ("ReScanner", "INFO", "ReScanner hat folgende Aufgaben bearbeitet: BASE"),
                                    ("ReScanner", "ERROR", "RePage can\'t be saved."))
                log_catcher.check_present(*expected_logging, order_matters=True)

    class WAITTask(ReScannerTask):
        def task(self):
            pass

    @skip("skipped after changing to CloudBot")
    @freeze_time("Jan 14th, 2020", auto_tick_seconds=1)
    def test_lemma_processed_are_saved(self):
        self._mock_surroundings()
        self.lemma_mock.return_value = [':RE:Lemma0', ':RE:Lemma1', ':RE:Lemma2']
        self.re_page_mock.side_effect = [ReDatenException, mock.DEFAULT, mock.DEFAULT, mock.DEFAULT, mock.DEFAULT]
        bot = ReScanner(log_to_screen=False, log_to_wiki=False)
        bot.tasks = [self.WAITTask]
        with bot:
            bot.run()
        # with open(bot.data.data_folder + os.sep + "ReScanner.data.json", encoding="utf-8") as data_file:
        #     data = json.load(data_file)
        #     self.assertEqual({":RE:Lemma1": mock.ANY, ":RE:Lemma2": mock.ANY},
        #                      data)
        #     self.assertLessEqual(datetime.strptime(data[":RE:Lemma1"], "%Y%m%d%H%M%S"),
        #                          datetime.strptime(data[":RE:Lemma2"], "%Y%m%d%H%M%S"))
        self.lemma_mock.return_value = [':RE:Lemma3', ":RE:Lemma4"]
        with bot:
            bot.run()
        # with open(bot.data.data_folder + os.sep + "ReScanner.data.json", encoding="utf-8") as data_file:
        #     data = json.load(data_file)
        #     self.assertEqual({":RE:Lemma1": mock.ANY, ":RE:Lemma2": mock.ANY,
        #                       ":RE:Lemma3": mock.ANY, ":RE:Lemma4": mock.ANY},
        #                      data)
        #     self.assertLess(datetime.strptime(data[":RE:Lemma1"], "%Y%m%d%H%M%S"),
        #                     datetime.strptime(data[":RE:Lemma2"], "%Y%m%d%H%M%S"))
        #     self.assertLess(datetime.strptime(data[":RE:Lemma2"], "%Y%m%d%H%M%S"),
        #                     datetime.strptime(data[":RE:Lemma3"], "%Y%m%d%H%M%S"))
        #     self.assertLess(datetime.strptime(data[":RE:Lemma3"], "%Y%m%d%H%M%S"),
        #                     datetime.strptime(data[":RE:Lemma4"], "%Y%m%d%H%M%S"))

    def test_reload_deprecated_lemma_data_none_there(self):
        self._mock_surroundings()
        self.lemma_mock.return_value = [":RE:Lemma1"]
        with suppress(AssertionError):
            with LogCapture() as log_catcher:
                with ReScanner(log_to_screen=False, log_to_wiki=False, debug=False):
                    expected_logging = (("ReScanner", "INFO", "Start the bot ReScanner."),
                                        ("ReScanner", "WARNING",
                                         "The last run wasn't successful. The data is thrown away."),
                                        ("ReScanner", "WARNING", "Try to get the deprecated data back."),
                                        ("ReScanner", "WARNING", "There isn't deprecated data to reload."))
                    log_catcher.check_present(*expected_logging, order_matters=True)

    @skip("skipped after changing to CloudBot")
    def test_reload_deprecated_lemma_data(self):
        self._mock_surroundings()
        self.lemma_mock.return_value = [":RE:Lemma1"]
        # with open(_DATA_PATH_TEST + os.sep + "ReScanner.data.json.deprecated", mode="w", encoding="utf-8") \
        #         as persist_json:
        #     json.dump({":RE:Lemma1": "20000101000000"}, persist_json)
        with suppress(AssertionError):
            with LogCapture() as log_catcher:
                with ReScanner(log_to_screen=False, log_to_wiki=False, debug=False):
                    log_catcher.check(("ReScanner", "INFO", "Start the bot ReScanner."),
                                      ("ReScanner", "WARNING",
                                       "The last run wasn't successful. The data is thrown away."),
                                      ("ReScanner", "WARNING", "Try to get the deprecated data back."))
