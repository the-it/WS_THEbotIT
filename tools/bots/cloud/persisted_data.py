import json
from collections.abc import Mapping
from datetime import datetime
from io import BytesIO
from typing import Dict, Any, Iterator

import boto3
from botocore import exceptions

from tools.bots import BotException
from tools.bots.cloud.base import get_aws_credentials, is_aws_test_env


class PersistedData(Mapping):
    def __init__(self, bot_name: str):
        self._data: Dict = {}
        self._bucket_name = f"wiki-bots-persisted-data-{'tst' if is_aws_test_env() else 'prd'}"
        key, secret = get_aws_credentials()
        self.s3_client = boto3.client("s3", aws_access_key_id=key, aws_secret_access_key=secret)
        self.s3_resource = boto3.resource("s3", aws_access_key_id=key, aws_secret_access_key=secret)
        self.bot_name: str = bot_name
        self.key_name: str = f"{bot_name}.data.json"

    def __getitem__(self, item) -> Any:
        return self._data[item]

    def __setitem__(self, key: str, value: Any):
        self._data[key] = value

    def __delitem__(self, key: str):
        del self._data[key]

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterator:
        return iter(self._data)

    def assign_dict(self, new_dict: Dict):
        if isinstance(new_dict, dict):
            self._data = new_dict
        else:
            raise BotException(f"{new_dict} has the wrong type. It must be a dictionary.")

    def dump(self, success: bool = True):
        key_name = self.key_name
        if not success:
            key_name += ".broken"
        self.s3_client.put_object(Bucket=self._bucket_name,
                                  Key=key_name,
                                  Body=BytesIO(json.dumps({"time": str(datetime.now()),
                                                           "data": self._data},
                                                          indent=2)
                                               .encode("utf-8")))

    def _load_from_bucket(self, key_appendix: str = ""):
        try:
            self._data = json.loads(
                self.s3_client.get_object(Bucket=self._bucket_name, Key=self.key_name + key_appendix)
                ["Body"].read().decode("utf-8"))["data"]  # type: ignore
        except exceptions.ClientError as error:
            if error.response['Error']['Code'] == 'NoSuchKey':
                raise BotException(f"The data for {self.key_name + key_appendix} doesn't exists") from error
            raise

    def _copy_to_deprecated(self):
        self.s3_resource.Object(self._bucket_name, f"{self.bot_name}.data.deprecated.json")\
            .copy_from(CopySource={'Bucket': self._bucket_name, 'Key': self.key_name})  # pylint: disable=no-member

    def load(self):
        self._load_from_bucket()
        self._copy_to_deprecated()

    def update(self, dict_to_update: Dict):
        self._data.update(dict_to_update)

    def get_broken(self):
        self._load_from_bucket(key_appendix=".broken")

    def get_deprecated(self):
        self._load_from_bucket(key_appendix=".deprecated")
