import json

from testfixtures import compare

from tools.bots import BotException
from tools.bots.cloud.persisted_data import PersistedData
from tools.bots.cloud.test_base import TestCloudBase

JSON_TEST = "{\n  \"a\": [\n    1,\n    2\n  ]\n}"
JSON_TEST_EXTEND = "{\n  \"a\": [\n    1,\n    2\n  ],\n  \"b\": 1\n}"
DATA_TEST = {"a": [1, 2]}
DATA_TEST_EXTEND = {"a": [1, 2], "b": 1}

BUCKET_NAME = "wiki_bots_persisted_data"

class TestPersistedData(TestCloudBase):
    def _make_json_file(self, filename: str = "TestBot.data.json", data: str = JSON_TEST):
        self.s3_client.put_object(Bucket=BUCKET_NAME, Key=filename, Body=data.encode("utf-8"))

    def setUp(self):
        super().setUp()
        self.data = PersistedData("TestBot")

    def test_load_from_bucket(self):
        self._make_json_file()
        self.data.load()
        compare(1, self.data["a"][0])
        deprecated_data = json.loads(self.s3_client.get_object(Bucket=BUCKET_NAME, Key="TestBot.data.json.deprecated")
            ["Body"].read().decode("utf-8"))
        compare(1, deprecated_data["a"][0])

    def test_load_from_bucket_no_data(self):
        with self.assertRaises(BotException):
            self.data.load()

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
