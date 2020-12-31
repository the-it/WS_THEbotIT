import os
from abc import ABC, abstractmethod
from pathlib import Path

BASE_PATH = Path("/mnt/temp_erik/re")

if not os.path.isdir(BASE_PATH):
    os.mkdir(BASE_PATH)


class DownloadTarget(ABC):
    @abstractmethod
    def get_source(self):
        pass

    @abstractmethod
    def get_target(self):
        pass
