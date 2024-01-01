# pylint: disable=protected-access,no-member,no-self-use
import typing
from unittest import TestCase

import boto3
from moto import mock_dynamodb, mock_s3

from tools.bots.cloud.base import is_aws_test_env

JSON_TEST = '{\n  "data": {\n    "a": [\n      1,\n      2\n    ]\n  },\n  "time": "2020-01-14 00:00:00"\n}'
JSON_TEST_EXTEND = '{\n  "data": {\n    "a": [\n      1,\n      2\n    ],\n    "b": 2\n  },' \
                   '\n  "time": "2020-01-14 00:00:00"\n}'
DATA_TEST = {'data': {'a': [1, 2]}, 'time': '2020-01-14 00:00:00'}
DATA_TEST_EXTEND = {'data': {'a': [1, 2], 'b': 2}, 'time': '2020-01-14 00:00:00'}
BUCKET_NAME = f"wiki-bots-persisted-data-{'tst' if is_aws_test_env() else 'prd'}"
TABLE_NAME = f"wiki_bots_manage_table_{'tst' if is_aws_test_env() else 'prd'}"


class TestCloudBase(TestCase):
    @classmethod
    @typing.no_type_check
    def setUpClass(cls) -> None:
        # mocking s3
        cls.mock_s3 = mock_s3()
        cls.mock_s3.start()
        cls.s3_client = boto3.client("s3")
        cls.s3 = boto3.resource("s3")
        cls._create_data_bucket()
        cls.data_bucket = cls.s3.Bucket(BUCKET_NAME)
        # mocking dynamodb
        cls.mock_dynamo = mock_dynamodb()
        cls.mock_dynamo.start()
        cls.dynamodb = boto3.resource("dynamodb", region_name="eu-central-1")
        cls._create_manage_table()
        cls.manage_table = cls.dynamodb.Table(TABLE_NAME)

    @classmethod
    @typing.no_type_check
    def tearDownClass(cls) -> None:
        cls.mock_s3.stop()
        cls.mock_dynamo.stop()

    @typing.no_type_check
    def _make_json_file(self, filename: str = "TestBot.data.json", data: str = JSON_TEST):
        self.s3_client.put_object(Bucket=BUCKET_NAME, Key=filename, Body=data.encode("utf-8"))

    def tearDown(self) -> None:
        self._truncate_manage_table()
        self.data_bucket.objects.all().delete()  # type: ignore

    @classmethod
    @typing.no_type_check
    def _create_data_bucket(cls) -> None:
        cls.s3.create_bucket(Bucket=BUCKET_NAME)

    @classmethod
    def _create_manage_table(cls):
        cls.dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {
                    "AttributeName": "bot_name",
                    "KeyType": "HASH"  # Partition key
                },
                {
                    "AttributeName": "start_time",
                    "KeyType": "RANGE"  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    "AttributeName": "bot_name",
                    "AttributeType": "S"
                },
                {
                    "AttributeName": "start_time",
                    "AttributeType": "S"
                }
            ],
            BillingMode="PAY_PER_REQUEST"
        )

    def _truncate_manage_table(self):
        scan = self.manage_table.scan()
        with self.manage_table.batch_writer() as batch:
            for each in scan["Items"]:
                batch.delete_item(
                    Key={
                        "bot_name": each["bot_name"],
                        "start_time": each["start_time"],
                    }
                )
