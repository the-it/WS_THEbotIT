import internetarchive
import requests

from service.ws_re.download.base import BASE_PATH, DownloadTarget
from service.ws_re.download.data import _ARCHIVES


class Quadrupel(DownloadTarget):
    def __init__(self, issue: str, page: int):
        self.issue = issue
        self.page = page

    def get_source(self):
        pass

    def download_file(url, local_filename):
        with requests.get(url, stream=True) as r:
            r.raise_for_status()  # Raise an error for bad status codes
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return local_filename

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
