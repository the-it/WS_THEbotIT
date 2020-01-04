import boto3
from boto3.dynamodb.conditions import Key
from mypy_boto3 import dynamodb

from tools.bots.cloud.status import Status


class StatusManager:
    MANAGE_TABLE = "wiki_bots_manage_table"

    def __init__(self, bot_name: str):
        self.dynamodb: dynamodb.DynamoDBServiceResource = boto3.resource('dynamodb', region_name='eu-central-1')
        self.manage_table = self.dynamodb.Table(self.MANAGE_TABLE)  # pylint: disable=no-member
        self.current_run = Status(self.manage_table.item_count, bot_name)
        self.bot_name = bot_name
        self.manage_table.put_item(Item=self.current_run.to_dict())  # type: ignore

    @property
    def last_runs(self):
        self
        self.manage_table.scan(FilterExpression=Key('bot_name').eq(self.bot_name))

