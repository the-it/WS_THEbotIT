import collections
import json
import re
from enum import Enum
from pathlib import Path
from typing import Union, Generator

import roman

from scripts.service.ws_re.template import ReDatenException


class VolumeType(Enum):
    FIRST_SERIES = 0
    SECOND_SERIES = 1
    SUPPLEMENTS = 2
    REGISTER = 3


_BASIC_REGEX = r"([IVX]{1,5})"
_REGEX_MAPPING = {VolumeType.FIRST_SERIES: re.compile("^" + _BASIC_REGEX + r"(?:,([1234]))?$"),
                  VolumeType.SECOND_SERIES: re.compile("^" + _BASIC_REGEX + r" A(?:,([12]))?$"),
                  VolumeType.SUPPLEMENTS: re.compile(r"^S " + _BASIC_REGEX + "$"),
                  VolumeType.REGISTER: re.compile(r"^R$")}


class Volume:
    def __init__(self, name: str, year: Union[str, int], start: str = None, end: str = None):
        self._name = name
        self._year = str(year)
        self._start = start
        self._end = end
        self._sortkey = self._compute_sortkey()

    def __repr__(self):  # pragma: no cover
        return f"<VOLUME - name:{self.name}, year:{self.year}, start:{self.start}, " \
               f"end:{self.end}, sort:{self.sort_key}>"

    @property
    def name(self) -> str:
        return self._name

    @property
    def file_name(self) -> str:
        return self.name.replace(",", "_")

    @property
    def year(self):
        return self._year

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    @property
    def type(self):
        for re_volume_type in _REGEX_MAPPING:
            if _REGEX_MAPPING[re_volume_type].match(self.name):
                return re_volume_type
        raise ReDatenException(f"Name of Volume {self.name} is malformed.")

    def _compute_sortkey(self):
        match = _REGEX_MAPPING[self.type].search(self.name)
        key = "4"
        latin_number = 0
        first_or_second_half = 0
        if self.name != "R":
            latin_number = roman.fromRoman(match.group(1))
            if self.type != VolumeType.SUPPLEMENTS:
                first_or_second_half = match.group(2) if match.group(2) else 0
        if self.type == VolumeType.FIRST_SERIES:
            key = f"1_{latin_number:02d}_{first_or_second_half}"
        elif self.type == VolumeType.SECOND_SERIES:
            key = f"2_{latin_number:02d}_{first_or_second_half}"
        elif self.type == VolumeType.SUPPLEMENTS:
            key = f"3_{latin_number:02d}"
        return key

    @property
    def sort_key(self) -> str:
        return self._sortkey


class Volumes(collections.MutableMapping):
    def __init__(self):
        path_to_file = Path(__file__).parent.joinpath("volumes.json")
        with open(str(path_to_file), encoding="utf-8") as json_file:
            _volume_list = json.load(json_file)
        _volume_mapping = collections.OrderedDict()
        for item in _volume_list:
            _volume_mapping[item["name"]] = Volume(**item)
        self._volume_mapping = _volume_mapping

    def __getitem__(self, item: str) -> Volume:
        try:
            return self._volume_mapping[item]
        except KeyError:
            raise ReDatenException(f"Register {item} doesn't exists")

    def __setitem__(self, key, value):
        pass

    def __delitem__(self, key):
        pass

    def __len__(self) -> int:
        return len(self._volume_mapping.keys())

    def __iter__(self) -> str:
        for key in self._volume_mapping:
            yield key

    def special_volume_iterator(self, volume_type: VolumeType) -> Generator[Volume, None, None]:
        for volume_key in self:
            volume = self[volume_key]
            if volume.type == volume_type:
                yield volume

    @property
    def first_series(self) -> Generator[Volume, None, None]:
        for volume in self.special_volume_iterator(VolumeType.FIRST_SERIES):
            yield volume

    @property
    def second_series(self) -> Generator[Volume, None, None]:
        for volume in self.special_volume_iterator(VolumeType.SECOND_SERIES):
            yield volume

    @property
    def supplements(self) -> Generator[Volume, None, None]:
        for volume in self.special_volume_iterator(VolumeType.SUPPLEMENTS):
            yield volume

    @property
    def register(self) -> Generator[Volume, None, None]:
        for volume in self.special_volume_iterator(VolumeType.REGISTER):
            yield volume

    @property
    def all_volumes(self) -> Generator[Volume, None, None]:
        for volume_key in self:
            yield self[volume_key]
