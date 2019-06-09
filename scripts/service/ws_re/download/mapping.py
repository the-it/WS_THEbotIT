import re
import shutil
from os import listdir, symlink, makedirs
from os.path import isfile, join
from pathlib import Path
from typing import Dict

from scripts.service.ws_re.download.base import DownloadTarget, BASE_PATH
from scripts.service.ws_re.download.raw_files import RawFiles
from scripts.service.ws_re.volumes import Volumes

_MAPPINGS = {
    "I,1": {"source": ("PaulyWissowa110", "Aal Apollokrates"), "pages": ((-1, 10010, 10370),)},
    "I,2": {"source": ("PaulyWissowa110", "Aal Apollokrates"), "pages": ((1439, 10370, 10735),)},
    "II,1": {"source": ("PaulyWissowa110", "Apollon Artemis"), "pages": ((-1, 30002, 30362),)},
    "II,2": {"source": ("PaulyWissowa110", "Artemisia Barbaroi"), "pages": ((1439, 40004, 40359),)},
    "III,1": {"source": ("PaulyWissowa110", "Barbarus Campanus"), "pages": ((-1, 50002, 50362),)},
    "III,2": {"source": ("PaulyWissowa110", "Campanus ager Claudius"), "pages": ((1439, 60002, 60004),
                                                                                 (1451, 60006, 60370))},
    "IV,1": {"source": ("PaulyWissowa110", "Claudius mons Cornificius"), "pages": ((-1, 70002, 70410),)},
    "IV,2": {"source": ("PaulyWissowa110", "Corniscae Demodoros"), "pages": ((1631, 80002, 80312),)},
    "V,1": {"source": ("PaulyWissowa110", "Demogenes Ephoroi"), "pages": ((-1, 90002, 90385),)},
    "V,2": {"source": ("PaulyWissowa110", "Demogenes Ephoroi"), "pages": ((1531, 90385, 90718),)},
    "VI,1": {"source": ("PaulyWissowa110", "Ephoros-Eutychos"), "pages": ((-1, 2, 386),)},
    "VI,2": {"source": ("PaulyWissowa110", "Euxantios-Fornaces"), "pages": ((1535, 2, 337),)},
    "VII,1": {"source": ("PaulyWissowa1120", "Fornax-Glykon"), "pages": ((-1, 2, 370),)},
    "VII,2": {"source": ("PaulyWissowa1120", "Glykyrrh-Helikeia"), "pages": ((1471, 2, 354),)},
    "VIII,1": {"source": ("PaulyWissowa1120", "Helikon-Hestia"), "pages": ((-1, 2, 330),)},
    "VIII,2": {"source": ("PaulyWissowa1120", "Hestiaia Hyagnis"), "pages": ((1311, 160002, 160331),)},
    "IX,1": {"source": ("PaulyWissowa1120", "Hyaia Imperator"), "pages": ((-1, 170002, 170301),)},
    "IX,2": {"source": ("PaulyWissowa1120", "Imperium Iugum"), "pages": ((1199, 180002, 180358),)},
    "X,1": {"source": ("PaulyWissowa1120", "Iugurtha Ius Latii"), "pages": ((-1, 190002, 190322),)},
    "X,2": {"source": ("PaulyWissowa1120", "Ius liberorum Katochos"), "pages": ((1279, 200002, 200318),)},
    "XI,1": {"source": ("PaulyWissowa1120", "Katoikoi Komoedie"), "pages": ((-1, 210002, 210322),)},
    "XI,2": {"source": ("PaulyWissowa1120", "Komogrammateus Kynegoi"), "pages": ((1279, 220002, 220314),)},
}


class Mapping(DownloadTarget):
    def __init__(self, target: str):
        self.target = target
        self.source = _MAPPINGS[target]["source"]
        self.path_raw_files = Path(BASE_PATH, "raw_files", *self.source)
        self.path_mapping = Path(BASE_PATH, "mappings",
                                 f"{Volumes()[self.target].sort_key.replace('_', '')}_{self.target}")

    def _get_raw_files_photo_mapping(self) -> Dict[int, str]:
        regex_number = re.compile(r"\d{4,6}")
        onlyfiles = [f for f in listdir(self.path_raw_files) if isfile(join(self.path_raw_files, f))]
        mapping = {}
        for file in onlyfiles:
            match = regex_number.search(file)
            if match:
                mapping[int(match.group(0))] = file
        return mapping

    def get_source(self):
        RawFiles(self.source[0]).get_target()

    def get_target(self):
        if not self.path_mapping.exists():
            print(f"Mapping {self.path_mapping} doesn't exists, produce it now ")
            self.get_source()
            _photo_mapping = self._get_raw_files_photo_mapping()
            try:
                for page_mapping in _MAPPINGS[self.target]["pages"]:
                    offset = page_mapping[0]
                    makedirs(self.path_mapping, exist_ok=True)
                    for idx, page in enumerate(range(page_mapping[1], page_mapping[2] + 1)):
                        try:
                            symlink(Path(self.path_raw_files, _photo_mapping[page]),
                                    Path(self.path_mapping, f"{offset + (4*idx)}.tif"))
                        except KeyError as error:
                            # known absent pages
                            if error.args[0] in (170260, 170265, 170270, 170275, 170280, 170285,
                                                 170290, 170291, 170292, 170295):
                                continue
                            raise error
            except KeyError as error:
                shutil.rmtree(self.path_mapping)
                raise error
        else:
            print(f"Mapping {self.path_mapping} exists")


if __name__ == "__main__":
    for key in _MAPPINGS:
        Mapping(key).get_target()
