# pylint: disable=protected-access,no-member,no-self-use
import json

from freezegun import freeze_time
from testfixtures import compare

from tools.bots import BotException
from tools.bots.cloud.persisted_data import PersistedData
from tools.bots.cloud.test_base import TestCloudBase, BUCKET_NAME


class TestPersistedData(TestCloudBase):
    def setUp(self):
        super().setUp()
        self.data = PersistedData("TestBot")

    def test_load_from_bucket_copy_to_deprecated(self):
        self._make_json_file()
        self.data.load()
        compare(1, self.data["a"][0])
        deprecated_data = json.loads(self.s3_client.get_object(Bucket=BUCKET_NAME, Key="TestBot.data.deprecated.json")
                                     ["Body"].read().decode("utf-8"))
        compare(1, deprecated_data["data"]["a"][0])

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
        self.data["tada"] = "tada"
        self.data.dump()
        data = json.loads(self.s3_client.get_object(Bucket=BUCKET_NAME, Key="TestBot.data.json")
                          ["Body"].read().decode("utf-8"))
        compare("tada", data["data"]["tada"])

    def test_dump_unsucessful(self):
        self._make_json_file()
        self.data.load()
        del self.data["a"]
        self.data["tada"] = "tada"
        self.data.dump(success=False)
        deprecated_data = json.loads(self.s3_client.get_object(Bucket=BUCKET_NAME, Key="TestBot.data.deprecated.json")
                                     ["Body"].read().decode("utf-8"))
        compare([1, 2], deprecated_data["data"]["a"])
        broken_data = json.loads(self.s3_client.get_object(Bucket=BUCKET_NAME, Key="TestBot.data.broken.json")
                                 ["Body"].read().decode("utf-8"))
        compare("tada", broken_data["data"]["tada"])

    def test_load_data_from_file_no_format(self):
        self._make_json_file(data='{"data":{"a":[1,2]},"time":"2020-01-14 00:00:00"}')
        self.data.load()
        self.assertEqual([1, 2], self.data["a"])

    def test_no_data_to_load(self):
        with self.assertRaises(BotException):
            self.data.load()
        self.assertFalse(self.data.keys())

    def test_for_boolean_value(self):
        self.data.assign_dict({})
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

    def test_clean_data(self):
        self._make_json_file()
        self.data.load()
        self.data["b"] = 2
        self.data.dump(success=False)
        new_run_data = PersistedData("TestBot")
        self.assertDictEqual({}, new_run_data._data)
        new_run_data["c"] = 3
        new_run_data.clean_data()
        with self.assertRaises(BotException):
            new_run_data.get_deprecated()
        self.assertDictEqual({}, new_run_data._data)

    def test_get_back_data_no_data_there(self):
        self._make_json_file()
        with self.assertRaises(BotException):
            self.data.get_deprecated()

    @freeze_time("2020-01-14")
    def test_persitence_date(self):
        self.data["data"] = "present"
        self.data.dump()
        data = json.loads(self.s3_client.get_object(Bucket=BUCKET_NAME, Key="TestBot.data.json")
                          ["Body"].read().decode("utf-8"))
        compare("2020-01-14 00:00:00", data["time"])
