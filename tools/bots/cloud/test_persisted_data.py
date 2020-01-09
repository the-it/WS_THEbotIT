from datetime import datetime

from tools.bots.cloud.test_base import teardown_data_path, TestCloudBase


class TestPersistedData(TestCloudBase):
    _precision = 0.001

    def setUp(self):
        setup_data_path(self)
        with open(_DATA_PATH_TEST + os.sep + "test_bot.last_run.json", mode="w") as persist_json:
            json.dump({"timestamp": "2000-01-01_00:00:00", "success": True}, persist_json)
        self.reference = datetime.now()

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
