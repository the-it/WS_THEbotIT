import re
from os import listdir, symlink, makedirs
from os.path import isfile, join
from pathlib import Path
from typing import Dict

from scripts.service.ws_re.download.base import DownloadTarget, BASE_PATH
from scripts.service.ws_re.download.raw_files import RawFiles
from scripts.service.ws_re.volumes import Volumes

_MAPPINGS = {
    "I,1": {"source": ("PaulyWissowa110", "Aal Apollokrates"), "start": (-1, 10010), "end": 10370},
    "I,2": {"source": ("PaulyWissowa110", "Aal Apollokrates"), "start": (1439, 10370), "end": 10735},
}


class Mapping(DownloadTarget):
    def __init__(self, target: str):
        self.target = target
        self.source = _MAPPINGS[target]["source"]
        self.path_raw_files = Path(BASE_PATH, "raw_files", *self.source)
        self.path_mapping = Path(BASE_PATH, "mappings",
                                 f"{Volumes()[self.target].sort_key}__{self.target}")

    def _get_raw_files_photo_mapping(self) -> Dict[int, str]:
        regex_number = re.compile(r"\d{6}")
        onlyfiles = [f for f in listdir(self.path_raw_files) if isfile(join(self.path_raw_files, f))]
        mapping = {}
        for file in onlyfiles:
            match = regex_number.search(file)
            if match:
                mapping[int(match.group(0))] = file
        return mapping

    def get_source(self):
        RawFiles(self.source[0]).get_target()

    def get_target(self):
        self.get_source()
        if not self.path_mapping.exists():
            _photo_mapping = self._get_raw_files_photo_mapping()
            offset = _MAPPINGS[self.target]["start"][0]
            makedirs(self.path_mapping, exist_ok=True)
            print(f"Mapping {self.path_mapping} doesn't exists, produce it now ")
            for idx, page in enumerate(range(_MAPPINGS[self.target]["start"][1], _MAPPINGS[self.target]["end"] + 1)):
                symlink(Path(self.path_raw_files, _photo_mapping[page]),
                        Path(self.path_mapping, f"{offset + (4*idx)}.tif"))
        else:
            print(f"Mapping {self.path_mapping} exists")


if __name__ == "__main__":
    for key in _MAPPINGS:
        Mapping(key).get_target()
