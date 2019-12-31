# pylint: disable=protected-access,no-member,no-self-use
from unittest import TestCase

import boto3
from moto import mock_dynamodb2


@mock_dynamodb2
class TestCloudBase(TestCase):
    def setUp(self) -> None:
        self.dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')
        self._create_manage_table()
        self.manage_table = self.dynamodb.Table('wiki_bots_manage_table_tst')

    def tearDown(self) -> None:
        self.manage_table.delete()

    def _create_manage_table(self):
        self.dynamodb.create_table(
            TableName='wiki_bots_manage_table_tst',
            KeySchema=[
                {
                    'AttributeName': 'id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'id',
                    'AttributeType': 'N'
                }
            ],
            BillingMode="PAY_PER_REQUEST"
        )

    def _truncate_manage_table(self):
        scan = self.table.scan()
        with self.table.batch_writer() as batch:
            for each in scan['Items']:
                batch.delete_item(
                    Key={
                        'uId': each['uId'],
                        'compId': each['compId']
                    }
                )
