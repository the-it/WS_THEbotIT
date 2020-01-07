# pylint: disable=protected-access,no-member,no-self-use
import time
from datetime import datetime
from unittest import mock

from testfixtures import compare

from tools.bots.cloud.status import Status
from tools.bots.cloud.status_manager import StatusManager
from tools.bots.cloud.test_base import TestCloudBase


class TestStatusManager(TestCloudBase):
    def test_init(self):
        status_manager = StatusManager("TestBot")
        compare(0, status_manager.current_run.id)
        compare({"id": 0,
                 "bot_name": "TestBot",
                 "finish": mock.ANY,
                 "success": mock.ANY,
                 "start_time": mock.ANY,
                 "finish_time": mock.ANY,
                 "output": mock.ANY},
                self.manage_table.get_item(Key={"id": 0, "bot_name": "TestBot"})["Item"])


    def test_unique_id(self):
        status_manager = StatusManager("TestBot")
        compare(0, status_manager.current_run.id)
        compare(0, self.manage_table.get_item(Key={"id": 0, "bot_name": "TestBot"})["Item"]["id"])
        status_manager_1 = StatusManager("TestBot1")
        compare(1, status_manager_1.current_run.id)
        compare(1, self.manage_table.get_item(Key={"id": 1, "bot_name": "TestBot1"})["Item"]["id"])
        status_manager_2 = StatusManager("TestBot")
        compare(2, status_manager_2.current_run.id)
        compare(2, self.manage_table.get_item(Key={"id": 2, "bot_name": "TestBot"})["Item"]["id"])

    def test_get_last_runs(self):
        StatusManager("TestBot")
        time.sleep(0.01)
        StatusManager("TestBot1")
        StatusManager("TestBot")
        status_manager_last_runs = StatusManager("TestBot")
        compare(2, len(status_manager_last_runs.last_runs))
        compare(2, status_manager_last_runs.last_runs[0].id)
        compare(0, status_manager_last_runs.last_runs[1].id)

    def test_get_last_finished_runs(self):
        manager = StatusManager("TestBot")
        manager.finish_run()
        StatusManager("TestBot")
        manager = StatusManager("TestBot")
        manager.finish_run(success=True)
        status_manager_last_runs = StatusManager("TestBot")
        compare(2, len(status_manager_last_runs.last_finished_runs))
        compare(2, status_manager_last_runs.last_finished_runs[0].id)
        compare(0, status_manager_last_runs.last_finished_runs[1].id)

    def test_get_last_successful_runs(self):
        manager = StatusManager("TestBot")
        manager.finish_run(success=True)
        manager = StatusManager("TestBot")
        manager.finish_run()
        manager = StatusManager("TestBot")
        manager.finish_run(success=True)
        status_manager_last_runs = StatusManager("TestBot")
        compare(2, len(status_manager_last_runs.last_successful_runs))
        compare(2, status_manager_last_runs.last_successful_runs[0].id)
        compare(0, status_manager_last_runs.last_successful_runs[1].id)

    def test_finish_run(self):
        manager = StatusManager("TestBot")
        manager.finish_run()
        last_item = Status.from_dict(self.manage_table.get_item(Key={"id": 0, "bot_name": "TestBot"})["Item"])
        compare(True, last_item.finish)
        self.assertGreater(last_item.finish_time, datetime.min)
        self.assertGreater(last_item.finish_time, last_item.start_time)

    def test_finish_success(self):
        manager = StatusManager("TestBot")
        manager.current_run.success = True
        manager.finish_run()
        last_item = Status.from_dict(self.manage_table.get_item(Key={"id": 0, "bot_name": "TestBot"})["Item"])
        compare(True, last_item.success)

        manager2 = StatusManager("TestBot")
        manager2.finish_run(success=True)
        last_item = Status.from_dict(self.manage_table.get_item(Key={"id": 1, "bot_name": "TestBot"})["Item"])
        compare(True, last_item.success)

    def test_finish_no_success(self):
        manager = StatusManager("TestBot")
        manager.finish_run()
        last_item = Status.from_dict(self.manage_table.get_item(Key={"id": 0, "bot_name": "TestBot"})["Item"])
        compare(False, last_item.success)
