import os
from abc import ABC, abstractmethod
from pathlib import Path
from sys import platform

BASE_PATH = None

if platform == "win32":
    BASE_PATH = Path("C:/RE")
elif platform in ("linux", "linux2"):
    BASE_PATH = Path("/home/erik/re")
else:
    raise NotImplementedError("the used os ist not implemented yet, please specify the path for your os.")

if not os.path.isdir(BASE_PATH):
    os.mkdir(BASE_PATH)


class DownloadTarget(ABC):
    @abstractmethod
    def get_source(self):
        pass

    @abstractmethod
    def get_target(self):
        pass
