from collections import Mapping
import json
import os
from shutil import rmtree
from unittest import TestCase, mock, skip

from tools.bots import BotExeption, PersistedData


class TestPersistedData(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestPersistedData, self).__init__(*args, **kwargs)
        self.data_path = os.getcwd() + os.sep + "data"
        self.json_test = "{\"a\": [1, 2]}"
        self.json_test_extend = "{\"a\": [1, 2], \"b\": 1}"
        self.data_test = {"a": [1, 2]}
        self.data_test_extend = {"a": [1, 2], "b": 1}

    def _remove_data_folder(self):
        if os.path.exists(self.data_path):
            rmtree(self.data_path)

    def _make_json_file(self, filename: str="TestBot.data.json", data: str=None):
        os.mkdir(self.data_path)
        with open(self.data_path + os.sep + filename, mode="w") as data_file:
            if not data:
                data = self.json_test
            data_file.write(data)

    def setUp(self):
        self._remove_data_folder()
        self.data = PersistedData("TestBot")

    def tearDown(self):
        self._remove_data_folder()

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
        os.mkdir(os.getcwd() + os.sep + "data")
        self.data.dump()
        self.assertTrue(os.path.isfile(self.data_path + os.sep + "TestBot.data.json"))

    def test_dump_value_is_correct(self):
        self.data.assign_dict(self.data_test)
        os.mkdir(os.getcwd() + os.sep + "data")
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
