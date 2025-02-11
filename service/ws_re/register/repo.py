import contextlib
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from git import Repo, GitError

REPO_URL = "git@github.com:the-it/re_register_data.git"
if "GITHUB_TOKEN" in os.environ:
    REPO_URL = f"https://{os.environ['GITHUB_TOKEN']}@github.com/the-it/re_register_data.git"
else:
    # read only access for CI
    REPO_URL = "https://github.com/the-it/re_register_data.git"

PATH_REAL_DATA = Path(__file__).parent.joinpath("data")
if "REGISTER_DATA_PATH" in os.environ:
    PATH_REAL_DATA = Path(os.environ["REGISTER_DATA_PATH"])
PATH_MOCK_DATA = Path(__file__).parent.joinpath("mock_data")


class DataRepo:
    data_is_real = True

    def __init__(self, update_repo: bool = False):
        self._git_repo = self._get_git_repo(update_repo)

    @classmethod
    def get_data_path(cls) -> Path:
        if cls.data_is_real:
            return PATH_REAL_DATA.joinpath("registers")
        return PATH_MOCK_DATA

    @classmethod
    def _get_git_repo(cls, update_repo) -> Optional[Repo]:
        if cls.data_is_real:
            try:
                repo = Repo(path=PATH_REAL_DATA)
                if update_repo:
                    repo.git.reset('--hard')
                    repo.remotes.origin.pull()
                return repo
            except GitError:
                with contextlib.suppress(FileNotFoundError):
                    shutil.rmtree(PATH_REAL_DATA)
                return Repo.clone_from(url=REPO_URL, to_path=PATH_REAL_DATA)
        return None

    def push(self) -> bool:
        if self._git_repo:
            if self._git_repo.index.diff(None):
                self._git_repo.git.add(str(PATH_REAL_DATA))
                now = datetime.now().strftime("%y%m%d_%H%M%S")
                self._git_repo.index.commit(f"Updating the register at {now}")
                self._git_repo.git.push("origin", self._git_repo.active_branch.name)
                return True
        return False

    @classmethod
    def mock_data(cls, mock: bool):
        cls.data_is_real = not mock
