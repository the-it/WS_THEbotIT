# pylint: disable=protected-access,no-member,no-self-use
from unittest import mock

from testfixtures import compare

from tools.bots.cloud.status_manager import StatusManager
from tools.bots.cloud.test_base import TestCloudBase

StatusManager.MANAGE_TABLE = "wiki_bots_manage_table_tst"


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
                self.manage_table.get_item(Key={"id": 0})["Item"])


    def test_unique_id(self):
        status_manager = StatusManager("TestBot")
        compare(0, status_manager.current_run.id)
        compare(0, self.manage_table.get_item(Key={"id": 0})["Item"]["id"])
        status_manager_1 = StatusManager("TestBot1")
        compare(1, status_manager_1.current_run.id)
        compare(1, self.manage_table.get_item(Key={"id": 1})["Item"]["id"])
        status_manager_2 = StatusManager("TestBot")
        compare(2, status_manager_2.current_run.id)
        compare(2, self.manage_table.get_item(Key={"id": 2})["Item"]["id"])
