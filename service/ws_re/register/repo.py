import contextlib
import shutil
from datetime import datetime
from pathlib import Path

from git import Repo, NoSuchPathError, InvalidGitRepositoryError

REPO_URL = "https://github.com/the-it/re_register_data"
PATH_REAL_DATA = Path(__file__).parent.joinpath("data")
PATH_MOCK_DATA = Path(__file__).parent.joinpath("mock_data")
MOCK_DATA = False


class DataRepo:
    def __init__(self):
        self._git_repo = self._get_git_repo()

    @property
    def data_path(self):
        if MOCK_DATA:
            return PATH_MOCK_DATA
        return PATH_REAL_DATA

    @staticmethod
    def _get_git_repo() -> Repo:
        if not MOCK_DATA:
            try:
                return Repo(path=PATH_REAL_DATA)
            except (NoSuchPathError, InvalidGitRepositoryError):
                with contextlib.suppress(FileNotFoundError):
                    shutil.rmtree(PATH_REAL_DATA)
                return Repo.clone_from(url=REPO_URL, to_path=PATH_REAL_DATA)

    def pull(self):
        if not MOCK_DATA:
            self._git_repo.git.reset('--hard')
            self._git_repo.remotes.origin.pull()

    def push(self) -> bool:
        if not MOCK_DATA:
            if self._git_repo.index.diff(None):
                self._git_repo.git.add(str(PATH_REAL_DATA))
                now = datetime.now().strftime("%y%m%d_%H%M%S")
                self._git_repo.index.commit(f"Updating the register at {now}")
                self._git_repo.git.push("origin", self._git_repo.active_branch.name)
                return  True
            return False
