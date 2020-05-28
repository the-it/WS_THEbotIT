# pylint: disable=protected-access
import json
import os
import time
from datetime import datetime, timedelta
from shutil import rmtree
from unittest import TestCase, mock

from testfixtures import LogCapture, compare

from tools.bots import BotException
from tools.bots.pi import CanonicalBot, OneTimeBot, PersistedTimestamp, PersistedData, \
    WikiLogger, \
    _DATA_PATH, _get_data_path

_DATA_PATH_TEST = _DATA_PATH + "_test"


def _remove_data_folder():
    if os.path.exists(_DATA_PATH_TEST):
        rmtree(_DATA_PATH_TEST)


def setup_data_path(test_class: TestCase):
    test_class.addCleanup(mock.patch.stopall)
    mock.patch("tools.bots.pi._DATA_PATH", _DATA_PATH_TEST).start()
    _remove_data_folder()
    os.mkdir(_DATA_PATH_TEST)


def teardown_data_path():
    _remove_data_folder()


class TestGetDataPath(TestCase):
    def setUp(self):
        setup_data_path(self)

    def tearDown(self):
        teardown_data_path()

    def test_folder_exist(self):
        with mock.patch("tools.bots.pi.os.mkdir") as mock_mkdir:
            self.assertEqual(_DATA_PATH_TEST, _get_data_path())
            mock_mkdir.assert_not_called()

    def test_make_folder(self):
        os.rmdir(_DATA_PATH_TEST)
        with mock.patch("tools.bots.pi.os.mkdir") as mock_mkdir:
            self.assertEqual(_DATA_PATH_TEST, _get_data_path())
            self.assertEqual(1, mock_mkdir.call_count)


class TestWikilogger(TestCase):
    def setUp(self):
        setup_data_path(self)
        self.logger = WikiLogger("test_bot", datetime(year=2000, month=1, day=1), log_to_screen=False)
        self.logger._setup_logger_properties()

    def tearDown(self):
        self.logger.tear_down()
        teardown_data_path()

    def test_logfile_names(self):
        self.assertDictEqual({"debug": "test_bot_DEBUG_000101000000.log", "info": "test_bot_INFO_000101000000.log"},
                             self.logger._get_logger_names())

    def test_log_message(self):
        self.logger.debug("debug")
        self.logger.info("info")
        with open(_DATA_PATH_TEST + os.sep + "test_bot_INFO_000101000000.log") as info_file:
            self.assertRegex(info_file.read(), r"\[\d\d:\d\d:\d\d\]\s\[INFO\s*?\]\s\[info\]\n")
        with open(_DATA_PATH_TEST + os.sep + "test_bot_DEBUG_000101000000.log") as info_file:
            self.assertRegex(info_file.read(), r"\[\d\d:\d\d:\d\d\]\s\[DEBUG\s*?\]\s\[debug\]\n"
                                               r"\[\d\d:\d\d:\d\d\]\s\[INFO\s*?\]\s\[info\]\n")

    def test_tear_down(self):
        self.logger.debug("debug")
        self.logger.info("info")
        self.assertTrue(os.path.isfile(_DATA_PATH_TEST + os.sep + "test_bot_INFO_000101000000.log"))
        self.assertTrue(os.path.isfile(_DATA_PATH_TEST + os.sep + "test_bot_DEBUG_000101000000.log"))
        self.logger.tear_down()
        self.assertFalse(os.path.isfile(_DATA_PATH_TEST + os.sep + "test_bot_INFO_000101000000.log"))
        self.assertTrue(os.path.isfile(_DATA_PATH_TEST + os.sep + "test_bot_DEBUG_000101000000.log"))

    def test_format_log_lines_for_wiki(self):
        self.logger.info("info")
        self.logger.warning("warning")
        self.logger.error("error")
        self.logger.critical("critical")
        expected_output = r"==00-01-01_00:00:00==\n\n" \
                          r"\[\d\d:\d\d:\d\d\]\s\[INFO\s*?\]\s\[info\]\n\n" \
                          r"\[\d\d:\d\d:\d\d\]\s\[WARNING\s*?\]\s\[warning\]\n\n" \
                          r"\[\d\d:\d\d:\d\d\]\s\[ERROR\s*?\]\s\[error\]\n\n" \
                          r"\[\d\d:\d\d:\d\d\]\s\[CRITICAL\s*?\]\s\[critical\]\n--~~~~"
        self.assertRegex(self.logger.create_wiki_log_lines(), expected_output)

    def test_exception(self):
        self.logger.exception("exception", Exception("test"))
        expected_output = r"==00-01-01_00:00:00==\n\n" \
                          r"\[\d\d:\d\d:\d\d\]\s\[ERROR\s*?\]\s\[exception\]\n\n" \
                          r"Exception: test\n--~~~~"
        self.assertRegex(self.logger.create_wiki_log_lines(), expected_output)


class TestPersistedTimestamp(TestCase):
    _precision = 0.001

    def setUp(self):
        setup_data_path(self)
        with open(_DATA_PATH_TEST + os.sep + "test_bot.last_run.json", mode="w") as persist_json:
            json.dump({"timestamp": "2000-01-01_00:00:00", "success": True}, persist_json)
        self.reference = datetime.now()
        self.timestamp = PersistedTimestamp("test_bot")

    def tearDown(self):
        teardown_data_path()

    def test_start_timestamp(self):
        self.assertAlmostEqual(self.reference.timestamp(),
                               self.timestamp.start_of_run.timestamp(),
                               delta=self._precision)

    def test_last_run_timestamp(self):
        self.timestamp.set_up()
        self.assertFalse(os.path.isfile(_DATA_PATH_TEST + os.sep + "test_bot.last_run.json"))
        self.assertAlmostEqual(datetime(year=2000, month=1, day=1).timestamp(),
                               self.timestamp.last_run.timestamp(),
                               delta=self._precision)
        self.assertAlmostEqual(self.reference.timestamp(),
                               self.timestamp.start_of_run.timestamp(),
                               delta=self._precision)

    def test_persist_timestamp(self):
        self.timestamp.success_this_run = True
        self.timestamp.tear_down()
        with open(_DATA_PATH_TEST + os.sep + "test_bot.last_run.json", mode="r") as filepointer:
            timestamp_dict = json.load(filepointer)
            self.assertTrue(timestamp_dict["success"])

    def test_persist_timestamp_false(self):
        self.timestamp.success_this_run = False
        self.timestamp.tear_down()
        timestamp = PersistedTimestamp("test_bot")
        self.assertFalse(timestamp.success_last_run)

    def test_no_timestamp_there(self):
        self.timestamp.set_up()
        os.mkdir(_DATA_PATH_TEST + os.sep + "test_bot.last_run.json")
        reference = datetime.now()
        timestamp = PersistedTimestamp("other_bot")
        self.assertFalse(timestamp.success_last_run)
        self.assertAlmostEqual(reference.timestamp(), timestamp.start_of_run.timestamp(), delta=self._precision)
        self.assertEqual(timestamp.last_run, datetime(1970, 1, 1))

    def test_devalidate_timestamp_of_last_run(self):
        self.timestamp.last_run = None

    def test_wrong_value_of_success_this_run(self):
        with self.assertRaises(TypeError):
            self.timestamp.success_this_run = 1


class TestOneTimeBot(TestCase):
    def setUp(self):
        setup_data_path(self)
        self.addCleanup(mock.patch.stopall)
        self.log_patcher = mock.patch.object(WikiLogger, "debug")
        self.timestamp_patcher = mock.patch.object(PersistedTimestamp, "debug")
        self.wiki_logger_mock = self.log_patcher.start()

    def tearDown(self):
        teardown_data_path()

    class MinimalBot(OneTimeBot):
        def task(self):
            pass

    def test_get_bot_name(self):
        self.assertEqual("MinimalBot", self.MinimalBot.get_bot_name())
        self.assertEqual("MinimalBot", self.MinimalBot().bot_name)

    # pylint: disable=abstract-method
    class NoTaskBot(OneTimeBot):
        pass

    def test_not_implemented(self):
        # pylint: disable=abstract-class-instantiated
        with self.assertRaises(TypeError):
            self.NoTaskBot()

    def test_basic_run(self):
        with self.MinimalBot(log_to_screen=False, log_to_wiki=False) as bot:
            bot.run()

    class LogBot(OneTimeBot):
        def task(self):
            self.logger.info("Test")
            time.sleep(0.001)

    def test_timestamp_return_start_time(self):
        with mock.patch("tools.bots.pi.PersistedTimestamp.start_of_run",
                        new_callable=mock.PropertyMock(return_value=datetime(2000, 1, 1))):
            with self.MinimalBot(log_to_screen=False, log_to_wiki=False) as bot:
                self.assertEqual(datetime(2000, 1, 1), bot.timestamp.start_of_run)
                bot.run()

    def test_timestamp_load_last_run(self):
        with open(_DATA_PATH_TEST + os.sep + "MinimalBot.last_run.json", mode="x", ) as persist_json:
            json.dump({"timestamp": "2000-01-01_00:00:00", "success": True}, persist_json)
        with self.MinimalBot(log_to_screen=False, log_to_wiki=False) as bot:
            self.assertEqual(datetime(2000, 1, 1), bot.timestamp.last_run)
            self.assertTrue(bot.timestamp.success_last_run)

        with open(_DATA_PATH_TEST + os.sep + "MinimalBot.last_run.json", mode="w") as persist_json:
            json.dump({"timestamp": "2000-01-01_00:00:00", "success": False}, persist_json)
        with self.MinimalBot(log_to_screen=False, log_to_wiki=False) as bot:
            self.assertFalse(bot.timestamp.success_last_run)

    class SuccessBot(OneTimeBot):
        def __init__(self, success=True, **kwargs):
            super().__init__(**kwargs)
            self.success_to_return = success

        def task(self):
            return self.success_to_return

    def test_timestamp_tear_down(self):
        with self.MinimalBot(log_to_screen=False, log_to_wiki=False) as bot:
            bot.run()
        with open(_DATA_PATH_TEST + os.sep + "MinimalBot.last_run.json", mode="r") as persist_json:
            run_dict = json.load(persist_json)
            self.assertFalse(run_dict["success"])

        with self.SuccessBot(success=True, log_to_screen=False, log_to_wiki=False) as bot:
            bot.run()
        with open(_DATA_PATH_TEST + os.sep + "SuccessBot.last_run.json", mode="r") as persist_json:
            run_dict = json.load(persist_json)
            self.assertTrue(run_dict["success"])

    def test_return_value_run(self):
        with self.SuccessBot(success=True, log_to_screen=False, log_to_wiki=False) as bot:
            self.assertTrue(bot.run())

        with self.SuccessBot(success=False, log_to_screen=False, log_to_wiki=False) as bot:
            self.assertFalse(bot.run())

    def test_logging(self):
        with LogCapture() as log_catcher:
            with self.LogBot(log_to_screen=False, log_to_wiki=False) as bot:
                # logging on enter
                log_catcher.check(("LogBot", "INFO", "Start the bot LogBot."))
                log_catcher.clear()
                bot.run()
                # logging on run
                log_catcher.check(("LogBot", "INFO", "Test"))
                log_catcher.clear()
            # logging on exit
            self.assertRegex(str(log_catcher), r"LogBot INFO\n  Finish bot LogBot in 0:00:00.\d{6}.")

    def test_watchdog(self):
        class WatchdogBot(OneTimeBot):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.timeout = timedelta(seconds=0.02)

            def task(self):
                while True:
                    if self._watchdog():
                        raise Exception("watchdog must not fire")  # pragma: no cover
                    time.sleep(0.04)
                    if self._watchdog():
                        return True
                    raise Exception("watchdog must fire")  # pragma: no cover

        with WatchdogBot(log_to_screen=False, log_to_wiki=False) as bot:
            self.assertTrue(bot.run())

    def test_send_log_to_wiki(self):
        with mock.patch("tools.bots.pi.Page") as mock_page:
            with self.MinimalBot(wiki=None, log_to_screen=False) as bot:
                bot.run()
            self.assertEqual(mock.call(None, "Benutzer:THEbotIT/Logs/MinimalBot"), mock_page.mock_calls[0])
            self.assertEqual(mock.call().text.__iadd__(mock.ANY), mock_page.mock_calls[1])
            self.assertEqual(mock.call().save("Update of Bot MinimalBot", botflag=True),
                             mock_page.mock_calls[2])

    def test_save_if_changed_positive(self):
        page_mock = mock.Mock()
        text_mock = mock.PropertyMock()
        type(page_mock).text = text_mock
        text_mock.return_value = "2"
        self.MinimalBot.save_if_changed(page_mock, "1", "changed")
        compare(mock.call.save("changed", botflag=True), page_mock.mock_calls[0])

    def test_save_if_changed_negativ(self):
        page_mock = mock.Mock()
        text_mock = mock.PropertyMock()
        type(page_mock).text = text_mock
        text_mock.return_value = "1"
        self.MinimalBot.save_if_changed(page_mock, "1", "changed")
        compare(0, len(page_mock.mock_calls))

        self.MinimalBot.save_if_changed(page_mock, "1 ", "changed")
        compare(0, len(page_mock.mock_calls))

    class ExceptionBot(OneTimeBot):
        def task(self):
            raise Exception("Exception")

    def test_throw_exception_in_task(self):
        with LogCapture() as log_catcher:
            with self.ExceptionBot(log_to_screen=False, log_to_wiki=False) as bot:
                log_catcher.clear()
                bot.run()
                log_catcher.check(("ExceptionBot", "ERROR", "Logging an uncaught exception"))
                self.assertFalse(bot.success)


JSON_TEST = "{\n  \"a\": [\n    1,\n    2\n  ]\n}"
JSON_TEST_EXTEND = "{\n  \"a\": [\n    1,\n    2\n  ],\n  \"b\": 1\n}"
DATA_TEST = {"a": [1, 2]}
DATA_TEST_EXTEND = {"a": [1, 2], "b": 1}


class TestPersistedData(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestPersistedData, self).__init__(*args, **kwargs)
        self.data_path = _DATA_PATH_TEST

    def _make_json_file(self, filename: str = "TestBot.data.json", data: str = JSON_TEST):
        with open(self.data_path + os.sep + filename, mode="w") as data_file:
            data_file.write(data)

    def setUp(self):
        setup_data_path(self)
        self.data = PersistedData("TestBot")

    def tearDown(self):
        teardown_data_path()

    def test_delete_key(self):
        self.data["a"] = 1
        del self.data["a"]
        with self.assertRaises(KeyError):
            dummy = self.data["a"]

    def test_iter_over_keys(self):
        self.data["a"] = [1, 2]
        self.data["b"] = 2
        iterator_over_keys = iter(self.data)
        test_set = set()
        test_set.add(next(iterator_over_keys))
        test_set.add(next(iterator_over_keys))
        self.assertSetEqual({"a", "b"}, test_set)
        self.assertEqual([1, 2], self.data["a"])
        self.assertEqual(2, self.data["b"])

    def test_assign_complete_dict(self):
        self.data["a"] = [1, 2]
        self.assertEqual([1, 2], self.data["a"])
        self.data.assign_dict({})
        self.assertTrue(isinstance(self.data, PersistedData))
        self.assertEqual({}, self.data)

    def test_assign_complete_dict_wrong_type(self):
        with self.assertRaises(BotException):
            self.data.assign_dict(1)

    def test_dump(self):
        self.data.dump()
        self.assertTrue(os.path.isfile(self.data_path + os.sep + "TestBot.data.json"))

    def test_dump_value_is_correct(self):
        self.data.assign_dict(DATA_TEST)
        self.data.dump()
        with open(self.data_path + os.sep + "TestBot.data.json", mode="r") as file:
            self.assertEqual(JSON_TEST, file.read())

    def test_dump_different_keys(self):
        self.data[1] = 1
        self.data["2"] = "2"
        self.data.dump()

    def test_load_data_from_file(self):
        self._make_json_file()
        self.data.load()
        self.assertEqual([1, 2], self.data["a"])

    def test_load_data_from_old_file(self):
        self._make_json_file(data="{\"a\": [1, 2]}")
        self.data.load()
        self.assertEqual([1, 2], self.data["a"])

    def test_no_data_to_load(self):
        with self.assertRaises(BotException):
            self.data.load()
        self.assertFalse(self.data.keys())

    def test_flag_old_file_as_deprecated(self):
        self._make_json_file()
        self.data.load()
        self.assertTrue(os.path.isfile(self.data_path + os.sep + "TestBot.data.json.deprecated"))
        self.assertFalse(os.path.isfile(self.data_path + os.sep + "TestBot.data.json"))

    def test_delete_old_data_file(self):
        self._make_json_file()
        self.data.load()
        with open(self.data_path + os.sep + "TestBot.data.json.deprecated", mode="r") as json_file:
            self.assertDictEqual(DATA_TEST, json.load(json_file))
        self.assertFalse(os.path.isfile(self.data_path + os.sep + "TestBot.data.json"))
        self.data["b"] = 1
        self.data.dump(True)
        with open(self.data_path + os.sep + "TestBot.data.json", mode="r") as json_file:
            self.assertDictEqual(DATA_TEST_EXTEND, json.load(json_file))
        self.assertFalse(os.path.isfile(self.data_path + os.sep + "TestBot.data.json.deprecated"))

    def test_flag_old_file_as_deprecated_keep_broken_file(self):
        self._make_json_file()
        self.data.load()
        with open(self.data_path + os.sep + "TestBot.data.json.deprecated", mode="r") as json_file:
            self.assertDictEqual(DATA_TEST, json.load(json_file))
        self.assertFalse(os.path.isfile(self.data_path + os.sep + "TestBot.data.json"))
        self.data["b"] = 1
        self.data.dump(False)
        self.assertFalse(os.path.isfile(self.data_path + os.sep + "TestBot.data.json"))
        with open(self.data_path + os.sep + "TestBot.data.json.deprecated", mode="r") as json_file:
            self.assertDictEqual(DATA_TEST, json.load(json_file))
        with open(self.data_path + os.sep + "TestBot.data.json.broken", mode="r") as json_file:
            self.assertDictEqual(DATA_TEST_EXTEND, json.load(json_file))

    def test_flag_data_as_broken(self):
        self._make_json_file()
        self.data.load()
        self.data["b"] = 2
        self.data.dump(success=False)
        self.assertTrue(os.path.isfile(self.data_path + os.sep + "TestBot.data.json.deprecated"))
        self.assertTrue(os.path.isfile(self.data_path + os.sep + "TestBot.data.json.broken"))
        with open(self.data_path + os.sep + "TestBot.data.json.broken", mode="r") as json_file:
            json_dict = json.load(json_file)
        self.assertEqual(2, json_dict["b"])
        with open(self.data_path + os.sep + "TestBot.data.json.deprecated", mode="r") as json_file:
            json_dict = json.load(json_file)
        self.assertEqual(["a"], list(json_dict.keys()))

    def test_for_boolean_value(self):
        self.data.assign_dict(dict())
        self.assertFalse(self.data)
        self.data[1] = 1
        self.assertTrue(self.data)
        del self.data[1]
        self.assertFalse(self.data)

    def test_update_data(self):
        self.data["a"] = 1
        self.data.update({"b": 2})
        self.assertDictEqual({"a": 1, "b": 2}, self.data._data)

    def test_get_back_from_broken(self):
        self._make_json_file()
        self.data.load()
        self.data["b"] = 2
        self.data.dump(success=False)
        new_run_data = PersistedData("TestBot")
        self.assertDictEqual({}, new_run_data._data)
        new_run_data.get_broken()
        self.assertDictEqual({"a": [1, 2], "b": 2}, new_run_data._data)

    def test_get_back_from_deprecated(self):
        self._make_json_file()
        self.data.load()
        self.data["b"] = 2
        self.data.dump(success=False)
        new_run_data = PersistedData("TestBot")
        self.assertDictEqual({}, new_run_data._data)
        new_run_data.get_deprecated()
        self.assertDictEqual({"a": [1, 2]}, new_run_data._data)

    def test_get_back_data_no_data_there(self):
        self._make_json_file()
        with self.assertRaises(BotException):
            self.data.get_deprecated()


class TestCanonicalBot(TestCase):
    def setUp(self):
        setup_data_path(self)
        self.addCleanup(mock.patch.stopall)
        self.log_patcher = mock.patch.object(WikiLogger, "debug")
        self.timestamp_patcher = mock.patch.object(PersistedTimestamp, "debug")
        self.wiki_logger_mock = self.log_patcher.start()

    def tearDown(self):
        teardown_data_path()

    @staticmethod
    def create_timestamp(bot_name, date=datetime(2000, 1, 1), success=True):
        with open(_DATA_PATH_TEST + os.sep + f"{bot_name}.last_run.json", mode="w") as persist_json:
            json.dump({"timestamp": date.strftime("%Y-%m-%d_%H:%M:%S"), "success": success}, persist_json)

    @staticmethod
    def create_data(bot_name, data=None):
        if not data:
            data = {"a": 1}
        with open(_DATA_PATH_TEST + os.sep + f"{bot_name}.data.json", mode="w") as persist_json:
            json.dump(data, persist_json)

    class MinimalCanonicalBot(CanonicalBot):
        def task(self):
            return True

    def test_basic_run(self):
        self.create_data("MinimalCanonicalBot")
        self.create_timestamp("MinimalCanonicalBot")
        with self.MinimalCanonicalBot(log_to_screen=False, log_to_wiki=False) as bot:
            bot.run()

    def test_load_and_store_data(self):
        self.create_data("MinimalCanonicalBot")
        self.create_timestamp("MinimalCanonicalBot")
        with self.MinimalCanonicalBot(log_to_screen=False, log_to_wiki=False) as bot:
            self.assertDictEqual({"a": 1}, bot.data._data)
            bot.run()
            bot.data["b"] = 2

        with self.MinimalCanonicalBot(log_to_screen=False, log_to_wiki=False) as bot:
            self.assertDictEqual({"a": 1, "b": 2}, bot.data._data)

    def test_last_run_failure(self):
        self.create_data("MinimalCanonicalBot")
        self.create_timestamp("MinimalCanonicalBot", success=False)
        with self.MinimalCanonicalBot(log_to_screen=False, log_to_wiki=False) as bot:
            self.assertDictEqual({}, bot.data._data)

    class DataOutdatedBot(CanonicalBot):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.new_data_model = datetime(2001, 1, 1)

        def task(self):
            return True

    def test_no_load_model_outdated(self):
        self.create_data("DataOutdatedBot")
        self.create_timestamp("DataOutdatedBot")
        with LogCapture() as log_catcher:
            with self.DataOutdatedBot(log_to_screen=False, log_to_wiki=False) as bot:
                log_catcher.check(("DataOutdatedBot", "INFO", "Start the bot DataOutdatedBot."),
                                  ("DataOutdatedBot", "WARNING", "The data is thrown away. It is out of date"))
                self.assertDictEqual({}, bot.data._data)
                bot.run()

    class DataThrowException(CanonicalBot):
        def task(self):
            raise Exception

    def test_keep_broken_data(self):
        self.create_data("DataThrowException")
        self.create_timestamp("DataThrowException")
        with LogCapture() as log_catcher:
            with mock.patch("tools.bots.pi.PersistedData.dump") as mock_dump:
                with self.DataThrowException(log_to_screen=False, log_to_wiki=False) as bot:
                    log_catcher.clear()
                    bot.run()
                mock_dump.assert_called_once_with(success=False)
                self.assertIn("DataThrowException CRITICAL\n"
                              "  There was an error in the general procedure. "
                              "The broken data and a backup of the old will be keept.",
                              str(log_catcher))

    def test_set_timestamp_for_searcher(self):
        self.create_timestamp("MinimalCanonicalBot")
        self.create_data("MinimalCanonicalBot")
        with self.MinimalCanonicalBot(log_to_screen=False, log_to_wiki=False) as bot:
            self.assertEqual(datetime(1999, 12, 31), bot.create_timestamp_for_search(1))

    def test_set_timestamp_for_searcher_no_successful_run(self):
        self.create_timestamp("MinimalCanonicalBot", success=False)
        self.create_data("MinimalCanonicalBot")
        with mock.patch("tools.bots.pi.PersistedTimestamp.start_of_run",
                        mock.PropertyMock(return_value=datetime(2001, 1, 1))):
            with self.MinimalCanonicalBot(log_to_screen=False, log_to_wiki=False) as bot:
                self.assertEqual(datetime(2000, 1, 1), bot.create_timestamp_for_search(10))

    def test_last_run_successful_true(self):
        self.create_timestamp("MinimalCanonicalBot", success=True)
        self.create_data("MinimalCanonicalBot")
        with self.MinimalCanonicalBot(log_to_screen=False, log_to_wiki=False) as bot:
            self.assertTrue(bot.last_run_successful)

    def test_last_run_successful_false_1(self):
        self.create_timestamp("MinimalCanonicalBot", success=False)
        self.create_data("MinimalCanonicalBot")
        with self.MinimalCanonicalBot(log_to_screen=False, log_to_wiki=False) as bot:
            self.assertFalse(bot.last_run_successful)

    def test_last_run_successful_false_2(self):
        with self.MinimalCanonicalBot(log_to_screen=False, log_to_wiki=False) as bot:
            self.assertFalse(bot.last_run_successful)

    def test_data_outdated(self):
        self.create_timestamp("DataOutdatedBot", date=datetime(2000, 12, 31))
        self.create_data("DataOutdatedBot")
        with self.DataOutdatedBot(log_to_screen=False, log_to_wiki=False) as bot:
            self.assertTrue(bot.data_outdated())
            self.assertDictEqual({}, bot.data._data)

    def test_data_outdated_not_outdated_1(self):
        self.create_timestamp("DataOutdatedBot", date=datetime(2001, 12, 31))
        self.create_data("DataOutdatedBot")
        with self.DataOutdatedBot(log_to_screen=False, log_to_wiki=False) as bot:
            self.assertFalse(bot.data_outdated())
            self.assertDictEqual({"a": 1}, bot.data._data)

    def test_data_outdated_not_outdated_2(self):
        self.create_data("DataOutdatedBot")
        with self.DataOutdatedBot(log_to_screen=False, log_to_wiki=False) as bot:
            self.assertTrue(bot.data_outdated())
            self.assertDictEqual({}, bot.data._data)
