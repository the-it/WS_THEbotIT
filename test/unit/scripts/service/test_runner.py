import os
from pathlib import Path
from shutil import rmtree, copy

from test import *
from scripts.runner import TheBotItScheduler


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

    def _copy_bot_to_run_dir(self, name: str):
        copy(str(Path(__file__).parent.joinpath("bots_for_scheduler", "{}.py".format(name))),
             str(self._get_one_time_run_test()))

    def _remove_temp_folder(self):
        if os.path.exists(str(self._get_archive_test())):
            rmtree(str(self._get_archive_test()))
        if os.path.exists(str(self._get_one_time_run_test())):
            rmtree(str(self._get_one_time_run_test()))

    def setUp(self):
        self._remove_temp_folder()
        self._create_dir_and_init(self._get_archive_test())
        self._create_dir_and_init(self._get_one_time_run_test())
        self.bot_it_scheduler = TheBotItScheduler(None, True)
        self.bot_it_scheduler.folder_one_time = "one_time_run_test"
        self.bot_it_scheduler.folder_archive = "archive_test"

    def tearDown(self):
        self._remove_temp_folder()

    def test_detect_files_to_run(self):
        self._copy_bot_to_run_dir("test_bot_1")
        self._copy_bot_to_run_dir("test_bot_2")
        print(self.bot_it_scheduler.path_one_time)
        # self.assertEqual(2, len(self.bot_it_scheduler._get_files_to_run()))
        self.assertIn("test_bot_1.py", self.bot_it_scheduler._get_files_to_run())
        self.assertIn("test_bot_2.py", self.bot_it_scheduler._get_files_to_run())
