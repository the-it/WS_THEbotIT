import boto3
from mypy_boto3 import dynamodb

from tools.bots.cloud.status import Status


class StatusManager:
    MANAGE_TABLE = "wiki_bots_manage_table"

    def __init__(self, bot_name: str):
        self.dynamodb: dynamodb.DynamoDBServiceResource = boto3.resource('dynamodb', region_name='eu-central-1')
        self.manage_table = self.dynamodb.Table(self.MANAGE_TABLE)  # pylint: disable=no-member
        # self.manage_table.query(ScanIndexForward=False, Limit=1)
        self.current_run = Status(self.manage_table.item_count, bot_name)
        self.manage_table.put_item(Item=self.current_run.to_dict())  # type: ignore
