from os import makedirs
from pathlib import Path

from PIL import Image

from service.ws_re.download_upload.base import BASE_PATH, DownloadTarget
from service.ws_re.download_upload.double import Double
from service.ws_re.volumes import Volumes


class Single(DownloadTarget):
    def __init__(self, issue: str, page: int):
        self.issue = issue
        self.page_1 = (page // 2 * 2) + 1
        self.page_2 = self.page_1 + 1
        self.path_issue = Path(BASE_PATH, "singles",
                               f"{Volumes()[self.issue].sort_key.replace('_', '')}_{self.issue}")
        self.path_page_2 = self.path_issue.joinpath(f"{self.page_2:04d}.png")
        self.path_page_1 = self.path_issue.joinpath(f"{self.page_1:04d}.png")
        self.double = Double(issue=self.issue, page=self.page_1)

    def get_source(self):
        self.double.get_target()

    def get_target(self):
        makedirs(self.path_issue, exist_ok=True)
        if not self.path_page_2.exists():
            print(f"Single {self.page_1}/{self.issue} doesn't exists, produce it now ")
            self.get_source()
            if self.page_1 % 4 == 3:
                double_image = Image.open(self.double.path_page_1)
            else:
                double_image = Image.open(self.double.path_page_2)
            (width, height) = double_image.size
            half_width = int(width / 2)
            list_of_colorsums = []
            range_slice = range(-200, 201, 1)
            # check every slice around the middle for the color value
            for j in range_slice:
                im = double_image.convert("L")
                crop_image = im.crop((half_width + j, 0, half_width + j + 1, height))
                list_of_colorsums.append(sum(list(crop_image.getdata())) / height)
            # the slice with the highest colorvalue should
            first_max_index = list_of_colorsums.index(max(list_of_colorsums))
            half = half_width + range_slice[first_max_index]
            single_image_1 = double_image.crop((0, 0, half, height))
            single_image_2 = double_image.crop((half, 0, width, height))
            single_image_1.save(self.path_page_1, "PNG")
            single_image_2.save(self.path_page_2, "PNG")


if __name__ == "__main__":
    volumes = Volumes()
    # issues = [
    #     "I A,1", "I A,2",
    #     "II A,1", "II A,2",
    #     "III A,1", "III A,2",
    #     "IV A,1", "IV A,2",
    #     "V A,1", "V A,2",
    #     "VI A,1", "VI A,2",
    #     "VII A,1", "VII A,2",
    #     "VIII A,1", "VIII A,2",
    #     "IX A,1", "IX A,2",
    #     "X A",
    #     "S I", "S II", "S III", "S IV", "S V",
    #     "S VI", "S VII", "S VIII", "S IX", "S X",
    #     "S XI", "S XII", "S XIII", "S XIV", "S XV",
    # ]
    issues = ["X,2"]
    for string in issues:
        volume = volumes[string]
        if volume.start_column and volume.end_column:
            for i in range(volume.start_column, volume.end_column + 1, 2):
                Single(issue=volume.name, page=i).get_target()
