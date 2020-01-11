import json
import os
from typing import Mapping, Dict, Any, Iterator

import boto3
from botocore.exceptions import ClientError

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
            with open(self.key_name, mode="w") as json_file:
                json.dump(self._data, json_file, indent=2)
            if os.path.isfile(self.key_name + ".deprecated"):
                os.remove(self.key_name + ".deprecated")
        else:
            with open(self.key_name + ".broken", mode="w") as json_file:
                json.dump(self._data, json_file, indent=2)

    def _load_from_bucket(self, key_appendix: str =""):
        try:
            self._data = json.loads(
                self.s3_client.get_object(Bucket=self._bucket_name + key_appendix, Key=self.key_name)
                ["Body"].read().decode("utf-8"))
        except ClientError as exception:
            if exception.response['Error']['Code'] == 'NoSuchKey':
                raise BotException(f"The data for {self._bucket_name + key_appendix} doesn't exists")
            else:
                raise

    def _copy_to_deprecated(self):
        self.s3_resource.Object(self._bucket_name, f"{self.key_name}.deprecated")\
            .copy_from(CopySource={'Bucket': self._bucket_name, 'Key': self.key_name})

    def load(self):
        self._load_from_bucket()
        self._copy_to_deprecated()

    def update(self, dict_to_update: Dict):
        self._data.update(dict_to_update)

    def _recover_data(self, type_of_data: str):
        try:
            with open(f"{self.key_name}.{type_of_data}", mode="r") as json_file:
                self.assign_dict(json.load(json_file))
        except FileNotFoundError:
            raise BotException(f"There is no {type_of_data} data to load.")

    def get_broken(self):
        self._load_from_bucket(key_appendix=".broken")

    def get_deprecated(self):
        self._load_from_bucket(key_appendix=".deprecated")
