import json
import os
from typing import Mapping, Dict, Any, Iterator

from tools.bots import BotException


class PersistedData(Mapping):
    def __init__(self, bot_name: str):
        self._data: Dict = {}
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

    def load(self):
        if os.path.exists(self.key_name):
            with open(self.key_name, mode="r") as json_file:
                self._data = json.load(json_file)
            os.rename(self.key_name, self.key_name + ".deprecated")
        else:
            raise BotException("No data to load.")

    def update(self, dict_to_update: Dict):
        self._data.update(dict_to_update)

    def _recover_data(self, type_of_data: str):
        try:
            with open(f"{self.key_name}.{type_of_data}", mode="r") as json_file:
                self.assign_dict(json.load(json_file))
        except FileNotFoundError:
            raise BotException(f"There is no {type_of_data} data to load.")

    def get_broken(self):
        self._recover_data("broken")

    def get_deprecated(self):
        self._recover_data("deprecated")
