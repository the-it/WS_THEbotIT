# pylint: disable=protected-access,no-member,no-self-use
import time
from datetime import datetime
from unittest import mock

from freezegun import freeze_time
from testfixtures import compare

from tools.bots.cloud.status_manager import StatusManager
from tools.bots.cloud.test_base import TestCloudBase


class TestStatusManager(TestCloudBase):
    @freeze_time("2001-01-01")
    def test_init(self):
        StatusManager("TestBot")
        compare({"bot_name": "TestBot",
                 "finish": mock.ANY,
                 "success": mock.ANY,
                 "start_time": "2001-01-01T00:00:00",
                 "finish_time": mock.ANY,
                 "output": mock.ANY},
                self.manage_table.get_item(Key={"bot_name": "TestBot", "start_time": "2001-01-01T00:00:00"})["Item"])

    @freeze_time("2001-01-01", auto_tick_seconds=60)
    def test_get_last_runs(self):
        StatusManager("TestBot")
        time.sleep(0.01)
        StatusManager("TestBot1")
        StatusManager("TestBot")
        status_manager_last_runs = StatusManager("TestBot")
        compare(2, len(status_manager_last_runs.last_runs))
        # newest entry first in array
        compare(datetime(year=2001, month=1, day=1, minute=4), status_manager_last_runs.last_runs[0].start_time)
        compare(datetime(year=2001, month=1, day=1, minute=0), status_manager_last_runs.last_runs[1].start_time)

    @freeze_time("2001-01-01", auto_tick_seconds=60)
    def test_get_last_run(self):
        no_run_status = StatusManager("TestBot")
        compare(None, no_run_status.last_run)
        one_run_status = StatusManager("TestBot")
        compare(None, no_run_status.last_run)
        compare(datetime(year=2001, month=1, day=1, minute=0), one_run_status.last_runs[0].start_time)

    @freeze_time("2001-01-01", auto_tick_seconds=60)
    def test_get_last_finished_runs(self):
        manager = StatusManager("TestBot")
        manager.finish_run()
        StatusManager("TestBot")
        manager = StatusManager("TestBot")
        manager.finish_run(success=True)
        status_manager_last_runs = StatusManager("TestBot")
        compare(2, len(status_manager_last_runs.last_finished_runs))
        # newest entry first in array
        compare(datetime(year=2001, month=1, day=1, minute=6),
                status_manager_last_runs.last_finished_runs[0].start_time)
        compare(datetime(year=2001, month=1, day=1, minute=0),
                status_manager_last_runs.last_finished_runs[1].start_time)

    @freeze_time("2001-01-01", auto_tick_seconds=60)
    def test_get_last_successful_runs(self):
        manager = StatusManager("TestBot")
        manager.finish_run(success=True)
        manager = StatusManager("TestBot")
        manager.finish_run()
        manager = StatusManager("TestBot")
        manager.finish_run(success=True)
        status_manager_last_runs = StatusManager("TestBot")
        compare(2, len(status_manager_last_runs.last_successful_runs))
        # newest entry first in array
        compare(datetime(year=2001, month=1, day=1, minute=8),
                status_manager_last_runs.last_successful_runs[0].start_time)
        compare(datetime(year=2001, month=1, day=1, minute=0),
                status_manager_last_runs.last_successful_runs[1].start_time)

    @freeze_time("2001-01-01", auto_tick_seconds=60)
    def test_finish_run(self):
        manager = StatusManager("TestBot")
        manager.finish_run()
        last_item = StatusManager("TestBot").last_run
        compare(True, last_item.finish)
        self.assertGreater(last_item.finish_time, datetime.min)
        self.assertGreater(last_item.finish_time, last_item.start_time)

    @freeze_time("2001-01-01", auto_tick_seconds=60)
    def test_finish_success(self):
        manager = StatusManager("TestBot")
        manager.current_run.success = True
        manager.finish_run()
        last_item = StatusManager("TestBot").last_run
        compare(True, last_item.success)

        manager2 = StatusManager("TestBot")
        manager2.finish_run(success=True)
        last_item = StatusManager("TestBot").last_run
        compare(True, last_item.success)

    @freeze_time("2001-01-01", auto_tick_seconds=60)
    def test_finish_no_success(self):
        manager = StatusManager("TestBot")
        manager.finish_run()
        last_item = StatusManager("TestBot").last_run
        compare(False, last_item.success)
