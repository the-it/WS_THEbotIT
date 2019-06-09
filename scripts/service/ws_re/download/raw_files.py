import os
from pathlib import Path

import patoolib

from scripts.service.ws_re.download.archive import Archive
from scripts.service.ws_re.download.base import DownloadTarget, BASE_PATH

_RAW_FILES = {
    "PaulySupp": "Pauly Supp.rar",
    "PaulyWissowa5466": "Pauly-Wissowa_54-66.rar",
    "PaulyWissowa4153": "Pauly-Wissowa_41-53.rar",
    "PaulyWissowa3140": "Pauly-Wissowa_31-40.rar",
    "PaulyWissowa2130": "Pauly-Wissowa_21-30.rar",
    "PaulyWissowa1120": "Pauly-Wissowa_11-20.rar",
    "PaulyWissowa110": "Pauly-Wissowa_1-10.rar",
}


class RawFiles(DownloadTarget):
    def __init__(self, target: str):
        self.target = target
        self.source = _RAW_FILES[self.target]

    def get_source(self):
        Archive(self.source).get_target()

    def get_target(self):
        path_raw_files = BASE_PATH.joinpath("raw_files").joinpath(self.target)
        if not path_raw_files.exists():
            print(f"Raw Files {path_raw_files} doesn't exists, unpack them now ")
            self.get_source()
            os.makedirs(path_raw_files, exist_ok=True)
            patoolib.extract_archive(str(Path(BASE_PATH, "archives", self.source)),
                                     outdir=str(path_raw_files),
                                     interactive=False)
        else:
            print(f"Raw Files {path_raw_files} exists")


if __name__ == "__main__":
    for key in _RAW_FILES:
        RawFiles(key).get_target()
