from os import makedirs
from pathlib import Path

from PIL import Image

from service.ws_re.download.base import BASE_PATH, DownloadTarget
from service.ws_re.download.data import _ARCHIVES
from service.ws_re.download.quadrupel import Quadrupel
from service.ws_re.volumes import Volumes


class Double(DownloadTarget):
    def __init__(self, issue: str, page: int):
        self.issue = issue
        self.page_2 = ((page + 2) // 4 * 4)+1
        self.page_1 = self.page_2 - 2
        self.path_issue = Path(BASE_PATH, "doubles",
                                 f"{Volumes()[self.issue].sort_key.replace('_', '')}_{self.issue}")
        self.path_page_2 = self.path_issue.joinpath(f"{self.page_2:04d}.png")
        self.path_page_1 = self.path_issue.joinpath(f"{self.page_1:04d}.png")
        self.quadrupel = Quadrupel(issue=self.issue, page=self.page_2)

    def get_source(self):
        self.quadrupel.get_target()

    def get_target(self):
        makedirs(self.path_issue, exist_ok=True)
        if not self.path_page_2.exists():
            self.get_source()
            quadrupel_image = Image.open(self.quadrupel.path_page)
            (width, height) = quadrupel_image.size
            half_width = int(width / 2)
            double_image_1 = quadrupel_image.crop((0, 0, half_width, height))
            double_image_2 = quadrupel_image.crop((half_width, 0, width, height))
            double_image_1.save(self.path_page_1, "PNG")
            double_image_2.save(self.path_page_2, "PNG")

if __name__ == "__main__":
    for key in _ARCHIVES:
        Double(issue="II,1", page=3).get_target()
