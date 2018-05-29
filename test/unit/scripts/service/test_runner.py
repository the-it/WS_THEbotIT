import os
from pathlib import Path
from shutil import rmtree, copy

from test import *
from test.unit.scripts.service.bots_for_scheduler.test_bot_1 import TestBot1
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
        file_list = self.bot_it_scheduler._get_files_to_run()
        self.assertEqual(2, len(file_list))
        self.assertIn("test_bot_1.py", file_list)
        self.assertIn("test_bot_2.py", file_list)

    def test_run_one_bot_from_file(self):
        self._copy_bot_to_run_dir("test_bot_1")
        with patch("scripts.runner.TheBotItScheduler.run_bot", new_callable=mock.Mock()) as run_mock:
            self.assertTrue(self.bot_it_scheduler.run_bot_from_file("test_bot_1.py"))
            compare(1, run_mock.call_count)
            self.assertTrue(isinstance(run_mock.mock_calls[0][1][0], TestBot1))
