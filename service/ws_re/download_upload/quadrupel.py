from os import makedirs
from pathlib import Path

import requests

from service.ws_re.download_upload.base import BASE_PATH, DownloadTarget
from service.ws_re.download_upload.data import _ARCHIVES
from service.ws_re.volumes import Volumes


class Quadrupel(DownloadTarget):
    def __init__(self, issue: str, page: int):
        self.issue = issue
        self.page = ((page + 2) // 4 * 4) + 1
        self.path_issue = Path(BASE_PATH, "quadruples",
                               f"{Volumes()[self.issue].sort_key.replace('_', '')}_{self.issue}")
        self.path_page = self.path_issue.joinpath(f"{self.page:04d}.png")

    def get_source(self):
        pass

    @staticmethod
    def download_file(url, local_filename):
        with requests.get(url, stream=True, timeout=2) as r:
            r.raise_for_status()  # Raise an error for bad status codes
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return local_filename

    def get_target(self):
        makedirs(self.path_issue, exist_ok=True)
        if not self.path_page.exists():
            self.download_file(url=f"https://elexikon.ch/meyers/RE/{self.issue}_{self.page}.png".replace(" ", ""),
                               local_filename=str(self.path_page))


if __name__ == "__main__":
    for key in _ARCHIVES:
        Quadrupel(issue="II,1", page=100).get_target()
