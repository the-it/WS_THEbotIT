import contextlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from git import Repo, NoSuchPathError, InvalidGitRepositoryError

REPO_URL = "https://github.com/the-it/re_register_data"
PATH_REAL_DATA = Path(__file__).parent.joinpath("data")
PATH_MOCK_DATA = Path(__file__).parent.joinpath("mock_data")


class DataRepo:
    data_is_real = True

    def __init__(self):
        self._git_repo = self._get_git_repo()

    @classmethod
    @property
    def data_path(cls):
        if cls.data_is_real:
            return PATH_REAL_DATA
        return PATH_MOCK_DATA

    @classmethod
    def _get_git_repo(cls) -> Optional[Repo]:
        if cls.data_is_real:
            try:
                return Repo(path=PATH_REAL_DATA)
            except (NoSuchPathError, InvalidGitRepositoryError):
                with contextlib.suppress(FileNotFoundError):
                    shutil.rmtree(PATH_REAL_DATA)
                return Repo.clone_from(url=REPO_URL, to_path=PATH_REAL_DATA)
        return None

    def pull(self):
        if self.data_is_real:
            self._git_repo.git.reset('--hard')
            self._git_repo.remotes.origin.pull()

    def push(self) -> bool:
        if self.data_is_real:
            if self._git_repo.index.diff(None):
                self._git_repo.git.add(str(PATH_REAL_DATA))
                now = datetime.now().strftime("%y%m%d_%H%M%S")
                self._git_repo.index.commit(f"Updating the register at {now}")
                self._git_repo.git.push("origin", self._git_repo.active_branch.name)
                return  True
        return False

    @classmethod
    def mock_data(cls, mock: bool):
        cls.data_is_real = not mock
