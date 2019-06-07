import os
from abc import ABC, abstractmethod
from pathlib import Path
from sys import platform

base_path = None

if platform == "win32":
    base_path = Path("C:/RE")
elif platform == "linux" or platform == "linux2":
    base_path = Path("/home/erik/re")
else:
    raise NotImplementedError("the used os ist not implemented yet, please specify the path for your os.")

if not os.path.isdir(base_path):
    os.mkdir(base_path)


class DownloadTarget(ABC):
    @abstractmethod
    def get_source(self):
        pass

    @abstractmethod
    def get_target(self):
        pass


