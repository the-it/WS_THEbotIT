import internetarchive

from scripts.service.ws_re.download.base import BASE_PATH, DownloadTarget
from scripts.service.ws_re.download.data import _ARCHIVES


class Archive(DownloadTarget):
    def __init__(self, target: str):
        self.target = target
        self.source = _ARCHIVES[target]

    def get_source(self):
        pass

    def get_target(self):
        path_archive = BASE_PATH.joinpath("archives").joinpath(self.target)
        if not path_archive.exists():
            print(f"Archive {path_archive} doesn't exists, download it now")
            session = internetarchive.ArchiveSession()
            download = session.get_item(self.source).get_file(self.target)
            download.download(str(path_archive))
        else:
            print(f"Archive {path_archive} exists")


if __name__ == "__main__":
    for key in _ARCHIVES:
        Archive(key).get_target()
