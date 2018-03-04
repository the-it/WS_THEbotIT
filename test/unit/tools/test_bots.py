from collections import Mapping
from datetime import datetime, timedelta
import json
import os
from shutil import rmtree
import time

from test import *
from tools.bots import BotExeption, OneTimeBot, PersistedTimestamp, PersistedData, WikiLogger, \
    _DATA_PATH, _get_data_path

_DATA_PATH_TEST = _DATA_PATH + "_test"


def _remove_data_folder():
    if os.path.exists(_DATA_PATH_TEST):
        rmtree(_DATA_PATH_TEST)


def _setup_data_path(test_class: TestCase):
    test_class.addCleanup(patch.stopall)
    patch("tools.bots._DATA_PATH", _DATA_PATH_TEST).start()
    _remove_data_folder()


def _teardown_data_path():
    _remove_data_folder()


class TestGetDataPath(TestCase):
    def setUp(self):
        _setup_data_path(self)

    def tearDown(self):
        _teardown_data_path()

    def test_folder_exist(self):
        os.mkdir(_DATA_PATH_TEST)
        with mock.patch("tools.bots.os.mkdir") as mock_mkdir:
            self.assertEqual(_DATA_PATH_TEST, _get_data_path())
            mock_mkdir.assert_not_called()

    def test_make_folder(self):
        with mock.patch("tools.bots.os.mkdir") as mock_mkdir:
            self.assertEqual(_DATA_PATH_TEST, _get_data_path())
            self.assertEqual(1, mock_mkdir.call_count)


class TestWikilogger(TestCase):
    def setUp(self):
        _setup_data_path(self)
        self.logger = WikiLogger("test_bot", datetime(year=2000, month=1, day=1), silence=True)

    def tearDown(self):
        self.logger.tear_down()
        _teardown_data_path()

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
        expected_output = r"==Log of 01\.01\.00 um 00:00:00==\n\n" \
                          r"\[\d\d:\d\d:\d\d\]\s\[INFO\s*?\]\s\[info\]\n\n" \
                          r"\[\d\d:\d\d:\d\d\]\s\[WARNING\s*?\]\s\[warning\]\n\n" \
                          r"\[\d\d:\d\d:\d\d\]\s\[ERROR\s*?\]\s\[error\]\n\n" \
                          r"\[\d\d:\d\d:\d\d\]\s\[CRITICAL\s*?\]\s\[critical\]\n--~~~~"
        self.assertRegex(self.logger.create_wiki_log_lines(), expected_output)

    def test_exception(self):
        try:
            raise Exception("test")
        except Exception as e:
            self.logger.exception("exception", e)
        expected_output = r"==Log of 01\.01\.00 um 00:00:00==\n\n" \
                          r"\[\d\d:\d\d:\d\d\]\s\[ERROR\s*?\]\s\[exception\]\n\n" \
                          r"Traceback \(most recent call last\):\n\n" \
                          r"File \".*?\", line \d{1,3}, in test_exception\n\n" \
                          r"raise Exception\(\"test\"\)\n\n" \
                          r"Exception: test\n--~~~~"
        self.assertRegex(self.logger.create_wiki_log_lines(), expected_output)


class TestPersistedTimestamp(TestCase):
    _precision = 0.001

    def setUp(self):
        _setup_data_path(self)
        os.mkdir(_DATA_PATH_TEST)
        with open(_DATA_PATH_TEST + os.sep + "test_bot.last_run.json", mode="w") as persist_json:
            json.dump({"timestamp": '2000-01-01_00:00:00', "success": True}, persist_json)
        self.reference = datetime.now()
        self.timestamp = PersistedTimestamp("test_bot")

    def tearDown(self):
        _teardown_data_path()

    def test_start_timestamp(self):
        self.assertAlmostEqual(self.reference.timestamp(), self.timestamp.start_of_run.timestamp(), delta=self._precision)

    def test_last_run_timestamp(self):
        self.assertFalse(os.path.isfile(_DATA_PATH_TEST + os.sep + "test_bot.last_run.json"))
        self.assertAlmostEqual(datetime(year=2000, month=1, day=1).timestamp(),
                               self.timestamp.last_run.timestamp(),
                               delta=self._precision)
        self.assertAlmostEqual(self.reference.timestamp(), self.timestamp.start_of_run.timestamp(), delta=self._precision)

    def test_persist_timestamp(self):
        self.timestamp.persist(success=True)
        with open(_DATA_PATH_TEST + os.sep + "test_bot.last_run.json", mode="r") as filepointer:
            timestamp_dict = json.load(filepointer)
            self.assertTrue(timestamp_dict["success"])

    def test_persist_timestamp_false(self):
        self.timestamp.persist(success=False)
        timestamp = PersistedTimestamp("test_bot")
        self.assertFalse(timestamp.success)

    def test_no_timestamp_there(self):
        os.mkdir(_DATA_PATH_TEST + os.sep + "test_bot.last_run.json")
        reference = datetime.now()
        timestamp = PersistedTimestamp("other_bot")
        self.assertFalse(timestamp.success)
        self.assertAlmostEqual(reference.timestamp(), timestamp.start_of_run.timestamp(), delta=self._precision)
        self.assertIsNone(timestamp.last_run)

    def test_devalidate_timestamp_of_last_run(self):
        self.timestamp.last_run = None


class TestOneTimeBot(TestCase):
    def setUp(self):
        _setup_data_path(self)
        self.addCleanup(patch.stopall)
        self.log_patcher = patch.object(WikiLogger, 'debug', autospec=True)
        self.timestamp_patcher = patch.object(PersistedTimestamp, 'debug', autospec=True)
        self.wiki_logger_mock = self.log_patcher.start()

    def tearDown(self):
        _teardown_data_path()

    class MinimalBot(OneTimeBot):
        def task(self):
            pass

    def test_get_bot_name(self):
        self.assertEqual("MinimalBot", self.MinimalBot.get_bot_name())
        self.assertEqual("MinimalBot", self.MinimalBot().bot_name)

    class NoTaskBot(OneTimeBot):
        pass

    def test_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            self.NoTaskBot()

    def test_basic_run(self):
        with self.MinimalBot(silence=True) as bot:
            bot.run()

    class LogBot(OneTimeBot):
        def task(self):
            self.logger.info("Test")
            time.sleep(0.1)

    @mock.patch("tools.bots.PersistedTimestamp.start_of_run", new_callable=mock.PropertyMock(return_value=datetime(2000, 1, 1)))
    def test_timestamp_return_start_time(self, mock_timestamp_start):
        with self.MinimalBot(silence=True) as bot:
            self.assertEqual(datetime(2000, 1, 1), bot.timestamp.start_of_run)
            bot.run()

    def test_timestamp_load_last_run(self):
        os.mkdir(_DATA_PATH_TEST)
        with open(_DATA_PATH_TEST + os.sep + "MinimalBot.last_run.json", mode="x", ) as persist_json:
            json.dump({"timestamp": '2000-01-01_00:00:00', "success": True}, persist_json)
        with self.MinimalBot(silence=True) as bot:
            self.assertEqual(datetime(2000, 1, 1), bot.timestamp.last_run)
            self.assertTrue(bot.timestamp.success)

        with open(_DATA_PATH_TEST + os.sep + "MinimalBot.last_run.json", mode="w") as persist_json:
            json.dump({"timestamp": '2000-01-01_00:00:00', "success": False}, persist_json)
        with self.MinimalBot(silence=True) as bot:
            self.assertFalse(bot.timestamp.success)

    class SuccessBot(OneTimeBot):
        def __init__(self, success=True, **kwargs):
            super().__init__(**kwargs)
            self.success_to_return = success

        def task(self):
            return self.success_to_return

    def test_timestamp_tear_down(self):
        with self.MinimalBot(silence=True) as bot:
            bot.run()
        with open(_DATA_PATH_TEST + os.sep + "MinimalBot.last_run.json", mode="r") as persist_json:
            run_dict = json.load(persist_json)
            self.assertFalse(run_dict["success"])

        with self.SuccessBot(success=True, silence=True) as bot:
            bot.run()
        with open(_DATA_PATH_TEST + os.sep + "SuccessBot.last_run.json", mode="r") as persist_json:
            run_dict = json.load(persist_json)
            self.assertTrue(run_dict["success"])

    def test_return_value_run(self):
        with self.SuccessBot(success=True, silence=True) as bot:
            self.assertTrue(bot.run())

        with self.SuccessBot(success=False, silence=True) as bot:
            self.assertFalse(bot.run())

    def test_logging(self):
        with LogCapture() as log_catcher:
            with self.LogBot(silence=True) as bot:
                # logging on enter
                log_catcher.check(('LogBot', 'INFO', 'Start the bot LogBot.'))
                log_catcher.clear()
                bot.run()
                # logging on run
                log_catcher.check(('LogBot', 'INFO', 'Test'))
                log_catcher.clear()
            # logging on exit
            self.assertRegex(str(log_catcher), r"LogBot INFO\n  Finish bot LogBot in 0:00:00.1\d{5}.")

    class WatchdogBot(OneTimeBot):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.timeout = timedelta(seconds=0.05)

        def task(self):
            while(True):
                if self._watchdog():
                    raise Exception("watchdog must not fire")
                time.sleep(0.1)
                if self._watchdog():
                    return True
                raise Exception("watchdog must fire")

    def test_watchdog(self):
        with self.WatchdogBot(silence=True) as bot:
            self.assertTrue(bot.run())



class TestPersistedData(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestPersistedData, self).__init__(*args, **kwargs)
        self.data_path = _DATA_PATH_TEST
        self.json_test = "{\n  \"a\": [\n    1,\n    2\n  ]\n}"
        self.json_test_extend = "{\n  \"a\": [\n    1,\n    2\n  ],\n  \"b\": 1\n}"
        self.data_test = {"a": [1, 2]}
        self.data_test_extend = {"a": [1, 2], "b": 1}

    def _make_json_file(self, filename: str="TestBot.data.json", data: str=None):
        with open(self.data_path + os.sep + filename, mode="w") as data_file:
            if not data:
                data = self.json_test
            data_file.write(data)

    def setUp(self):
        _setup_data_path(self)
        self.data = PersistedData("TestBot")

    def tearDown(self):
        _teardown_data_path()

    def test_is_mapping(self):
        self.assertTrue(isinstance(self.data, Mapping))

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
        with self.assertRaises(BotExeption):
            self.data.assign_dict(1)

    def test_dump(self):
        self.data.dump()
        self.assertTrue(os.path.isfile(self.data_path + os.sep + "TestBot.data.json"))

    def test_dump_value_is_correct(self):
        self.data.assign_dict(self.data_test)
        self.data.dump()
        with open(self.data_path + os.sep + "TestBot.data.json", mode="r") as file:
            self.assertEqual(self.json_test, file.read())

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
        with self.assertRaises(BotExeption):
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
            self.assertDictEqual(self.data_test, json.load(json_file))
        self.assertFalse(os.path.isfile(self.data_path + os.sep + "TestBot.data.json"))
        self.data["b"] = 1
        self.data.dump(True)
        with open(self.data_path + os.sep + "TestBot.data.json", mode="r") as json_file:
            self.assertDictEqual(self.data_test_extend, json.load(json_file))
        self.assertFalse(os.path.isfile(self.data_path + os.sep + "TestBot.data.json.deprecated"))

    def test_flag_old_file_as_deprecated_keep_broken_file(self):
        self._make_json_file()
        self.data.load()
        with open(self.data_path + os.sep + "TestBot.data.json.deprecated", mode="r") as json_file:
            self.assertDictEqual(self.data_test, json.load(json_file))
        self.assertFalse(os.path.isfile(self.data_path + os.sep + "TestBot.data.json"))
        self.data["b"] = 1
        self.data.dump(False)
        self.assertFalse(os.path.isfile(self.data_path + os.sep + "TestBot.data.json"))
        with open(self.data_path + os.sep + "TestBot.data.json.deprecated", mode="r") as json_file:
            self.assertDictEqual(self.data_test, json.load(json_file))
        with open(self.data_path + os.sep + "TestBot.data.json.broken", mode="r") as json_file:
            self.assertDictEqual(self.data_test_extend, json.load(json_file))

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
        self.assertDictEqual({"a": 1, "b": 2}, self.data.data)
