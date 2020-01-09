# pylint: disable=protected-access,no-member,no-self-use
import os
from shutil import rmtree
from unittest import TestCase, mock

import boto3
from moto import mock_dynamodb2, mock_s3

from tools.bots.cloud.base import TMP_WIKI_BOT_PATH, get_data_path


def teardown_data_path():
    if os.path.exists(TMP_WIKI_BOT_PATH):
        rmtree(TMP_WIKI_BOT_PATH)

def setup_data_path():
    teardown_data_path()
    os.mkdir(TMP_WIKI_BOT_PATH)


class TestGetDataPath(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pass

    @classmethod
    def tearDownClass(cls) -> None:
        pass

    def setUp(self):
        setup_data_path()

    def tearDown(self):
        teardown_data_path()

    def test_folder_exist(self):
        with mock.patch("tools.bots.pi.os.mkdir") as mock_mkdir:
            self.assertEqual(TMP_WIKI_BOT_PATH, get_data_path())
            mock_mkdir.assert_not_called()

    def test_make_folder(self):
        os.rmdir(TMP_WIKI_BOT_PATH)
        with mock.patch("tools.bots.pi.os.mkdir") as mock_mkdir:
            self.assertEqual(TMP_WIKI_BOT_PATH, get_data_path())
            self.assertEqual(1, mock_mkdir.call_count)


@mock_s3
@mock_dynamodb2
class TestCloudBase(TestCase):
    def setUp(self) -> None:
        self.dynamodb = boto3.resource("dynamodb", region_name="eu-central-1")
        self.s3_client = boto3.client("s3")
        self.s3 = boto3.resource("s3")
        self._create_manage_table()
        self._create_data_bucket()
        self.manage_table = self.dynamodb.Table("wiki_bots_manage_table")
        self.data_bucket = self.s3.Bucket("wiki_bots_persisted_data")

    def tearDown(self) -> None:
        self.manage_table.delete()
        self.data_bucket.delete()

    def _create_data_bucket(self) -> None:
        self.s3.create_bucket(Bucket="wiki_bots_persisted_data")

    def _create_manage_table(self):
        self.dynamodb.create_table(
            TableName="wiki_bots_manage_table",
            KeySchema=[
                {
                    "AttributeName": "id",
                    "KeyType": "HASH"  # Partition key
                },
                {
                    "AttributeName": "bot_name",
                    "KeyType": "RANGE"  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    "AttributeName": "id",
                    "AttributeType": "N"
                },
                {
                    "AttributeName": "bot_name",
                    "AttributeType": "S"
                }
            ],
            BillingMode="PAY_PER_REQUEST"
        )

    def _truncate_manage_table(self):
        scan = self.table.scan()
        with self.table.batch_writer() as batch:
            for each in scan["Items"]:
                batch.delete_item(
                    Key={
                        "uId": each["uId"],
                        "compId": each["compId"]
                    }
                )
