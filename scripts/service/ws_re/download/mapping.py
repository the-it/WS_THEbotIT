from pathlib import Path

from scripts.service.ws_re.download.base import DownloadTarget, base_path
from scripts.service.ws_re.download.raw_files import RawFiles

_mappings  = {
    "I,1": {"source": ("PaulyWissowa110", "Aal Apollokrates")}
}

class Mapping(DownloadTarget):
    def __init__(self, target: str):
        self.target = target
        self.source = _mappings[target]["source"]

    def get_source(self):
        RawFiles(self.source[0]).get_target()

    def get_target(self):
        self.get_source()
        source_path = Path(base_path, "raw_files", *self.source)


if __name__ == "__main__":
    for key in _mappings:
        Mapping(key).get_target()

