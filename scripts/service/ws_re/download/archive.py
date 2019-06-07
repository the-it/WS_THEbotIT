import internetarchive

from scripts.service.ws_re.download.base import base_path, DownloadTarget

_archives = {
    "Pauly Supp.rar": "PaulySupp",
    "Pauly-Wissowa_54-66.rar": "PaulyWissowa5466",
    "Pauly-Wissowa_41-53.rar": "PaulyWissowa4153_201412",
    "Pauly-Wissowa_31-40.rar": "PaulyWissowa3140_201412",
    "Pauly-Wissowa_21-30.rar": "PaulyWissowa2130",
    "Pauly-Wissowa_11-20.rar": "PaulyWissowa1120",
    "Pauly-Wissowa_1-10.rar": "PaulyWissowa110",
             }


class Archive(DownloadTarget):
    def __init__(self, target: str):
        self.target = target
        self.source = _archives[target]

    def get_source(self):
        pass

    def get_target(self):
        path_archive = base_path.joinpath("archives").joinpath(self.target)
        if not path_archive.exists():
            print(f"Archive {path_archive} doesn't exists, download it now")
            session = internetarchive.ArchiveSession()
            download = session.get_item(self.source).get_file(self.target)
            download.download(str(path_archive))
        else:
            print(f"Archive {path_archive} exists")

if __name__ == "__main__":
    for key in _archives:
        Archive(key).get_target()
