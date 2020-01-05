from datetime import datetime
from typing import List

import boto3
from boto3.dynamodb.conditions import Key
from mypy_boto3 import dynamodb

from tools.bots.cloud.status import Status


class StatusManager:
    MANAGE_TABLE = "wiki_bots_manage_table"

    def __init__(self, bot_name: str):
        self._dynamodb: dynamodb.DynamoDBServiceResource = boto3.resource('dynamodb', region_name='eu-central-1')
        self._manage_table = self._dynamodb.Table(self.MANAGE_TABLE)  # pylint: disable=no-member
        self.current_run = Status(self._manage_table.item_count, bot_name)
        self.bot_name = bot_name
        self._manage_table.put_item(Item=self.current_run.to_dict())  # type: ignore
        self._last_runs = []

    @property
    def last_runs(self) -> List[Status]:
        if not self._last_runs:
            raw_list = self._manage_table.scan(FilterExpression=Key('bot_name').eq(self.bot_name))["Items"][:-1]
            self._last_runs = [Status.from_dict(status_dict) for status_dict in raw_list[::-1]]
        return self._last_runs

    @property
    def last_finished_runs(self) -> List[Status]:
        return [status for status in self.last_runs if status.finish]

    @property
    def last_successful_runs(self) -> List[Status]:
        return [status for status in self.last_runs if status.success]

    def finish_run(self, success: bool =False):
        self.current_run.finish = True
        self.current_run.finish_time = datetime.now()
        if success:
            self.current_run.success = success
        self._manage_table.put_item(Item=self.current_run.to_dict())  # type: ignore

