import os
from pathlib import Path

import patoolib

from scripts.service.ws_re.download.archive import Archive
from scripts.service.ws_re.download.base import DownloadTarget, BASE_PATH
from scripts.service.ws_re.download.data import _RAW_FILES


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
