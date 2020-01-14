import json
from collections.abc import Mapping
from datetime import datetime
from typing import Dict, Any, Iterator

import boto3
from botocore import exceptions

from tools.bots import BotException


class PersistedData(Mapping):
    def __init__(self, bot_name: str):
        self._data: Dict = {}
        self._bucket_name = "wiki_bots_persisted_data"
        self.s3_client = boto3.client("s3")
        self.s3_resource = boto3.resource("s3")
        self.bot_name: str = bot_name
        self.key_name: str = bot_name + ".data.json"

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
        if success:
            self.s3_client.put_object(Bucket=self._bucket_name,
                                      Key=self.key_name,
                                      Body=json.dumps({"time": str(datetime.now()), "data": self._data}, indent=2)
                                      .encode("utf-8"))
        else:
            self.s3_client.put_object(Bucket=self._bucket_name,
                                      Key=self.key_name + ".broken",
                                      Body=json.dumps({"time": str(datetime.now()), "data": self._data}, indent=2)
                                      .encode("utf-8"))

    def _load_from_bucket(self, key_appendix: str = ""):
        try:
            self._data = json.loads(
                self.s3_client.get_object(Bucket=self._bucket_name, Key=self.key_name + key_appendix)
                ["Body"].read().decode("utf-8"))["data"]  # type: ignore
        except exceptions.ClientError as exception:
            if exception.response['Error']['Code'] == 'NoSuchKey':
                raise BotException(f"The data for {self._bucket_name + key_appendix} doesn't exists")
            raise

    def _copy_to_deprecated(self):
        self.s3_resource.Object(self._bucket_name, f"{self.key_name}.deprecated")\
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
