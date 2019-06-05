import internetarchive

from .base import base_path

_archives = {
    "PaulySupp": "Pauly Supp.rar",
    "PaulyWissowa5466": "Pauly-Wissowa_54-66.rar",
    "PaulyWissowa4153_201412": "Pauly-Wissowa_41-53.rar",
    "PaulyWissowa3140_201412": "Pauly-Wissowa_31-40.rar",
    "PaulyWissowa2130": "Pauly-Wissowa_21-30.rar",
    "PaulyWissowa1120": "Pauly-Wissowa_11-20.rar",
    "PaulyWissowa110": "Pauly-Wissowa_1-10.rar",
             }


class Archive():
    def __init__(self, target: str):
        self.target = target
        self.source = _archives[target]

    def get_target(self):
        session = internetarchive.ArchiveSession()
        download = session.get_item(self.source).get_file(self.target)
        download.download(base_path.joinpath("archives").joinpath(self.source))
