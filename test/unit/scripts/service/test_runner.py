import os
from pathlib import Path
from shutil import rmtree

from test import *
from tools.bots import CanonicalBot, BotExeption
from tools.bot_scheduler import BotScheduler


class TestBotScheduler(TestCase):
    def _get_path_for_scripts(self) -> Path:
        path = Path(__file__)
        repo_root = path.parent.parent.parent.parent.parent
        scripts = repo_root.joinpath("scripts")
        self.assertTrue(os.path.isdir(str(scripts)))
        return scripts

    def _get_archive_test(self) -> Path:
        return self._get_path_for_scripts().joinpath("archive_test")

    def _get_one_time_run_test(self) -> Path:
        return self._get_path_for_scripts().joinpath("one_time_run_test")

    @staticmethod
    def _create_dir_and_init(path: Path):
        os.mkdir(str(path))
        open(str(path.joinpath("init.py")), 'w').close()

    def setUp(self):
        self._create_dir_and_init(self._get_archive_test())
        self._create_dir_and_init(self._get_one_time_run_test())

    def tearDown(self):
        rmtree(str(self._get_archive_test()))
        rmtree(str(self._get_one_time_run_test()))

    def test_1(self):
        pass
