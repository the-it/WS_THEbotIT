import boto3

from tools.bots.cloud.status import Status


class StatusManager:
    MANAGE_TABLE = "wiki_bots_manage_table"

    def __init__(self, bot_name: str):
        self.dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')
        self.manage_table = self.dynamodb.Table(self.MANAGE_TABLE)
        self.current_run = Status(1, bot_name)
        self.manage_table.put_item(Item=self.current_run.to_dict())
