from datetime import datetime
from typing import List, Optional

import boto3
from boto3.dynamodb.conditions import Key
from mypy_boto3_dynamodb import DynamoDBServiceResource

from tools.bots.cloud.status import Status

MANAGE_TABLE = "wiki_bots_manage_table"


class StatusManager:
    def __init__(self, bot_name: str):
        self._dynamodb: DynamoDBServiceResource = boto3.resource('dynamodb', region_name='eu-central-1')
        self._manage_table = self._dynamodb.Table(MANAGE_TABLE)  # pylint: disable=no-member
        self.current_run = Status(self._manage_table.item_count, bot_name)
        self.bot_name = bot_name
        self._manage_table.put_item(Item=self.current_run.to_dict())  # type: ignore
        self._last_runs: List[Status] = []

    @property
    def last_runs(self) -> List[Status]:
        if not self._last_runs:
            raw_list = self._manage_table.scan(FilterExpression=Key('bot_name').eq(self.bot_name))  # type: ignore
            self._last_runs = [Status.from_dict(status_dict)
                               for status_dict
                               in raw_list["Items"][:-1][::-1]
                               if status_dict["id"] != self.current_run.id]
        return self._last_runs

    @property
    def last_run(self) -> Optional[Status]:
        if self.last_runs:
            return self.last_runs[0]
        return None

    @property
    def last_finished_runs(self) -> List[Status]:
        return [status for status in self.last_runs if status.finish]

    @property
    def last_successful_runs(self) -> List[Status]:
        return [status for status in self.last_runs if status.success]

    @property
    def last_successful_run(self) -> Optional[Status]:
        if self.last_successful_runs:
            return self.last_successful_runs[0]
        return None

    def finish_run(self, success: bool = False):
        self.current_run.finish = True
        self.current_run.finish_time = datetime.now()
        if success:
            self.current_run.success = success
        self._manage_table.put_item(Item=self.current_run.to_dict())  # type: ignore
