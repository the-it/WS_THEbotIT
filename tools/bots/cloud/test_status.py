# pylint: disable=protected-access,no-self-use
import time
from datetime import datetime, timedelta
from unittest import TestCase, mock

from testfixtures import compare

from tools.bots.cloud.status import Status


class TestStatus(TestCase):
    def test_init(self):
        # bot_name is a necessary parameter
        with self.assertRaises(TypeError):
            Status(id=1)  # pylint: disable=no-value-for-parameter
        # id is a necessary parameter
        with self.assertRaises(TypeError):
            Status(bot_name="TestBot")  # pylint: disable=no-value-for-parameter
        status = Status(id=1, bot_name="TestBot")
        compare(1, status.id)
        compare("TestBot", status.bot_name)
        compare(False, status.success)
        compare(False, status.finish)

    def test_from_dict(self):
        status = Status.from_dict({"id": 2,
                                   "bot_name": "TestBot",
                                   "start_time": '2000-01-01T00:00:00',
                                   "finish_time": '2000-01-01T00:10:00'
                                   })
        compare(2, status.id)
        compare("TestBot", status.bot_name)
        compare(datetime(year=2000, month=1, day=1), status.start_time)
        compare(datetime(year=2000, month=1, day=1, minute=10), status.finish_time)

    def test_to_dict(self):
        status = Status(id=1, bot_name="TestBot")
        compare({"id": 1,
                 "bot_name": "TestBot",
                 "success": False,
                 "finish": False,
                 "start_time": mock.ANY,
                 "finish_time": '0001-01-01T00:00:00',
                 "output": None},
                status.to_dict())

    def test_create_start_time(self):
        now = datetime.now()
        status = Status(id=1, bot_name="TestBot")
        self.assertTrue(timedelta(seconds=0.001) > abs(now - status.start_time))
        compare(datetime.min, status.finish_time)

    def test_close_run_timestamp(self):
        now = datetime.now()
        status = Status(id=1, bot_name="TestBot")
        time.sleep(0.002)
        status.close_run(success=False, finish=False)
        self.assertTrue(timedelta(seconds=0.004) > abs(now - status.finish_time))
        self.assertTrue(timedelta(seconds=0) < abs(now - status.finish_time))

    def test_finish_success(self):
        status = Status(id=4, bot_name="TestBot")
        return_dict = status.close_run(success=True, finish=True)
        compare(True, status.finish)
        compare(True, status.success)
        compare({"id": 4,
                 "bot_name": "TestBot",
                 "success": True,
                 "finish": True,
                 "start_time": mock.ANY,
                 "finish_time": mock.ANY,
                 "output": None},
                return_dict)

    def test_output(self):
        status = Status(id=4, bot_name="TestBot")
        compare(None, status.output)
        status.output = {"a": 1, "b": ["c", "d"]}
        compare({"a": 1, "b": ["c", "d"]}, status.to_dict()["output"])
