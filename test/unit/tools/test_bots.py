from collections import Mapping
from datetime import datetime
import json
import os
from shutil import rmtree
import time

from test import *
from tools.bots import BotExeption, PersistedTimestamp, PersistedData, WikiLogger, _get_data_path

_data_path = os.getcwd() + os.sep + "data"


def _remove_data_folder():
    if os.path.exists(_data_path):
        rmtree(_data_path)


class TestGetDataPath(TestCase):
    def setUp(self):
        _remove_data_folder()

    def test_folder_exist(self):
        os.mkdir(_data_path)
        with mock.patch("tools.bots.os.mkdir") as mock_mkdir:
            self.assertEqual(_data_path, _get_data_path())
            mock_mkdir.assert_not_called()

    def test_make_folder(self):
        with mock.patch("tools.bots.os.mkdir") as mock_mkdir:
            self.assertEqual(_data_path, _get_data_path())
            mock_mkdir.assert_called_once()


class TestWikilogger(TestCase):
    def setUp(self):
        _remove_data_folder()
        self.logger = WikiLogger("test_bot", datetime(year=2000, month=1, day=1))

    def tearDown(self):
        self.logger.tear_down()
        _remove_data_folder()

    def test_logfile_names(self):
        self.assertDictEqual({"debug": "test_bot_DEBUG_000101000000.log", "info": "test_bot_INFO_000101000000.log"},
                             self.logger._get_logger_names())

    def test_log_message(self):
        self.logger.debug("debug")
        self.logger.info("info")
        with open("data/test_bot_INFO_000101000000.log") as info_file:
            self.assertRegex(info_file.read(), r"\[\d\d:\d\d:\d\d\]\s\[INFO\s*?\]\s\[info\]\n")
        with open("data/test_bot_DEBUG_000101000000.log") as info_file:
            self.assertRegex(info_file.read(), r"\[\d\d:\d\d:\d\d\]\s\[DEBUG\s*?\]\s\[debug\]\n"
                                               r"\[\d\d:\d\d:\d\d\]\s\[INFO\s*?\]\s\[info\]\n")

    def test_tear_down(self):
        self.logger.debug("debug")
        self.logger.info("info")
        self.assertTrue(os.path.isfile("data/test_bot_INFO_000101000000.log"))
        self.assertTrue(os.path.isfile("data/test_bot_DEBUG_000101000000.log"))
        self.logger.tear_down()
        self.assertFalse(os.path.isfile("data/test_bot_INFO_000101000000.log"))
        self.assertTrue(os.path.isfile("data/test_bot_DEBUG_000101000000.log"))

    def test_format_log_lines_for_wiki(self):
        self.logger.info("info")
        self.logger.warning("warning")
        self.logger.error("error")
        expected_output = r"==Log of 01\.01\.00 um 00:00:00==\n\n" \
                          r"\[\d\d:\d\d:\d\d\]\s\[INFO\s*?\]\s\[info\]\n\n" \
                          r"\[\d\d:\d\d:\d\d\]\s\[WARNING\s*?\]\s\[warning\]\n\n" \
                          r"\[\d\d:\d\d:\d\d\]\s\[ERROR\s*?\]\s\[error\]\n--~~~~"
        self.assertRegex(self.logger.create_wiki_log_lines(), expected_output)


class TestPersistedTimestamp(TestCase):
    _precision = 0.001

    def setUp(self):
        _remove_data_folder()
        os.mkdir("data")
        with open("data/test_bot.last_run.json", mode="w") as persist_json:
            json.dump({"last_run": '2000-01-01_00:00:00'}, persist_json)
        self.reference = datetime.now()
        self.timestamp = PersistedTimestamp("test_bot")

    def tearDown(self):
        _remove_data_folder()

    def test_start_timestamp(self):
        self.assertAlmostEqual(self.reference.timestamp(), self.timestamp.start.timestamp(), delta= self._precision)

    def test_last_run_timestamp(self):
        self.assertFalse(os.path.isfile("data/test_bot.last_run.json"))
        self.assertAlmostEqual(datetime(year=2000, month=1, day=1).timestamp(),
                               self.timestamp.last_run.timestamp(),
                               delta=self._precision)
        self.assertAlmostEqual(self.reference.timestamp(), self.timestamp.start.timestamp(), delta=self._precision)


class TestPersistedData(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestPersistedData, self).__init__(*args, **kwargs)
        self.data_path = _data_path
        self.json_test = "{\"a\": [1, 2]}"
        self.json_test_extend = "{\"a\": [1, 2], \"b\": 1}"
        self.data_test = {"a": [1, 2]}
        self.data_test_extend = {"a": [1, 2], "b": 1}

    def _make_json_file(self, filename: str="TestBot.data.json", data: str=None):
        with open(self.data_path + os.sep + filename, mode="w") as data_file:
            if not data:
                data = self.json_test
            data_file.write(data)

    def setUp(self):
        _remove_data_folder()
        self.data = PersistedData("TestBot")

    def tearDown(self):
        _remove_data_folder()

    def test_is_mapping(self):
        self.assertTrue(isinstance(self.data, Mapping))

    def test_iter_over_keys(self):
        self.data["a"] = [1, 2]
        self.data["b"] = 2
        iterator_over_keys = iter(self.data)
        self.assertEqual("a", next(iterator_over_keys))
        self.assertEqual([1, 2], self.data["a"])
        self.assertEqual("b", next(iterator_over_keys))
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

    def test_dump_and_create_folder(self):
        self.data.dump()

    def test_load_data_from_file(self):
        self._make_json_file()
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
