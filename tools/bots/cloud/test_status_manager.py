# pylint: disable=protected-access,no-member,no-self-use
import decimal
from unittest import TestCase

import boto3
from moto import mock_dynamodb2


@mock_dynamodb2
class TestStatusManager(TestCase):
    def test_run(self):
        dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')

        dynamodb.create_table(
            TableName='Movies',
            KeySchema=[
                {
                    'AttributeName': 'year',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'title',
                    'KeyType': 'RANGE'  # Sort key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'year',
                    'AttributeType': 'N'
                },
                {
                    'AttributeName': 'title',
                    'AttributeType': 'S'
                },

            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
            }
        )
        table = dynamodb.Table('Movies')

        title = "The Big New Movie"
        year = 2015

        table.put_item(
            Item={
                'year': year,
                'title': title,
                'info': {
                    'plot': "Nothing happens at all.",
                    'rating': decimal.Decimal(0)
                }
            }
        )
