from datetime import datetime
from importlib import import_module
import os
from pathlib import Path
from shutil import rmtree, copy
import sys
import time

from git import Repo

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
        open(str(path.joinpath("__init__.py")), 'w').close()

    @skipIf(sys.platform.startswith("win"), "I don't know what is wrong here ... but windows is unable to find this file.")
    def _copy_bot_to_run_dir(self, name: str):
        copy(str(Path(__file__).parent.joinpath("bots_for_scheduler", "{}.py".format(name))),
             str(self._get_one_time_run_test()))
        time.sleep(0.01)

    def _copy_bot_to_archive_dir(self, name: str):
        copy(str(Path(__file__).parent.joinpath("bots_for_scheduler", "{}.py".format(name))),
             str(self._get_archive_test()))

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
        os.mkdir(str(self._get_one_time_run_test().joinpath("testfolder")))
        file_list = self.bot_it_scheduler._get_files_to_run()
        self.assertEqual(2, len(file_list))
        self.assertIn("test_bot_1.py", file_list)
        self.assertIn("test_bot_2.py", file_list)

    def test_run_one_bot_from_file(self):
        self._copy_bot_to_run_dir("test_bot_1")
        with patch.object(self.bot_it_scheduler, "run_bot", mock.Mock(return_value=True)) as run_mock:
            self.assertTrue(self.bot_it_scheduler._run_bot_from_file("test_bot_1.py"))
            compare(1, run_mock.call_count)
            compare(type(run_mock.mock_calls[0][1][0]).__name__, "TestBot1")

    def test_run_two_bots_from_file(self):
        self._copy_bot_to_run_dir("test_bot_34")
        # both runs successfule
        with patch.object(self.bot_it_scheduler, "run_bot", mock.Mock(return_value=True)) as run_mock:
            self.assertTrue(self.bot_it_scheduler._run_bot_from_file("test_bot_34.py"))
            compare(2, run_mock.call_count)
            compare(type(run_mock.mock_calls[0][1][0]).__name__, "TestBot3")
            compare(type(run_mock.mock_calls[1][1][0]).__name__, "TestBot4")
        # second run with errors
        with patch.object(self.bot_it_scheduler, "run_bot", mock.Mock(side_effect=[True, False])) as run_mock:
            self.assertFalse(self.bot_it_scheduler._run_bot_from_file("test_bot_34.py"))
            compare(2, run_mock.call_count)
            compare(type(run_mock.mock_calls[0][1][0]).__name__, "TestBot3")
            compare(type(run_mock.mock_calls[1][1][0]).__name__, "TestBot4")
        # first run with errors
        with patch.object(self.bot_it_scheduler, "run_bot", mock.Mock(side_effect=[False, True])) as run_mock:
            self.assertFalse(self.bot_it_scheduler._run_bot_from_file("test_bot_34.py"))
            compare(2, run_mock.call_count)
            compare(type(run_mock.mock_calls[0][1][0]).__name__, "TestBot3")
            compare(type(run_mock.mock_calls[1][1][0]).__name__, "TestBot4")

    def test_move_file_folder_exists(self):
        self._copy_bot_to_run_dir("test_bot_1")
        now = datetime.today()
        path_to_current_archive = str(self._get_archive_test().joinpath(str(now.year)))
        os.mkdir(path_to_current_archive)
        self.bot_it_scheduler._move_file_to_archive("test_bot_1.py")
        self.assertIn("test_bot_1.py", os.listdir(path_to_current_archive))
        with open(path_to_current_archive + os.sep + "test_bot_1.py", "r") as bot_file:
            compare(StringComparison("\# successful processed on {}".format(now.strftime("%Y-%m-%d"))), bot_file.readline())

    def test_move_file_folder_not_exists(self):
        self._copy_bot_to_run_dir("test_bot_1")
        path_to_current_archive = str(self._get_archive_test().joinpath(str(datetime.today().year)))
        # os.mkdir(path_to_current_archive), don't create the folder
        self.bot_it_scheduler._move_file_to_archive("test_bot_1.py")
        self.assertIn("test_bot_1.py", os.listdir(path_to_current_archive))

    def test_change_repo(self):
        self._copy_bot_to_archive_dir("test_bot_1")
        with patch("scripts.runner.git.Repo", mock.Mock(spec=Repo)) as repo_mock:
            self.bot_it_scheduler._push_files(["test_bot_1.py"])
            file_add = [str(self._get_archive_test().joinpath(str(datetime.today().year), "test_bot_1.py"))]
            file_remove = [str(self._get_one_time_run_test().joinpath("test_bot_1.py"))]
            compare(mock.call(search_parent_directories=True), repo_mock.mock_calls[0])
            compare("().index.add", repo_mock.mock_calls[1][0])
            compare(file_add, repo_mock.mock_calls[1][1][0])
            compare("().index.remove", repo_mock.mock_calls[2][0])
            compare(file_remove, repo_mock.mock_calls[2][1][0])
            compare("().index.commit", repo_mock.mock_calls[3][0])
            compare("move successful bot scripts: test_bot_1.py", repo_mock.mock_calls[3][1][0])
            compare("().remote", repo_mock.mock_calls[4][0])
            compare("origin", repo_mock.mock_calls[4][1][0])
            compare("().remote().push", repo_mock.mock_calls[5][0])

    def test_change_repo_two_bots(self):
        self._copy_bot_to_archive_dir("test_bot_1")
        self._copy_bot_to_archive_dir("test_bot_2")
        with patch("scripts.runner.git.Repo", mock.Mock(spec=Repo)) as repo_mock:
            self.bot_it_scheduler._push_files(["test_bot_1.py", "test_bot_2.py"])
            file_add = [str(self._get_archive_test().joinpath(str(datetime.today().year), "test_bot_1.py")),
                        str(self._get_archive_test().joinpath(str(datetime.today().year), "test_bot_2.py"))]
            file_remove = [str(self._get_one_time_run_test().joinpath("test_bot_1.py")),
                           str(self._get_one_time_run_test().joinpath("test_bot_2.py"))]
            compare(mock.call(search_parent_directories=True), repo_mock.mock_calls[0])
            compare("().index.add", repo_mock.mock_calls[1][0])
            compare(file_add, repo_mock.mock_calls[1][1][0])
            compare("().index.remove", repo_mock.mock_calls[2][0])
            compare(file_remove, repo_mock.mock_calls[2][1][0])
            compare("().index.commit", repo_mock.mock_calls[3][0])
            compare("move successful bot scripts: test_bot_1.py, test_bot_2.py", repo_mock.mock_calls[3][1][0])
            compare("().remote", repo_mock.mock_calls[4][0])
            compare("origin", repo_mock.mock_calls[4][1][0])
            compare("().remote().push", repo_mock.mock_calls[5][0])

    def test_complete_task(self):
        self._copy_bot_to_run_dir("test_bot_1")
        self._copy_bot_to_run_dir("test_bot_2")
        with patch("tools.bot_scheduler.BotScheduler.task", mock.Mock()) as super_mock:
            with patch.object(self.bot_it_scheduler, "_run_bot_from_file", mock.Mock(side_effect=[True, False])) as run_mock:
                with patch.object(self.bot_it_scheduler, "_push_files", mock.Mock(side_effect=[True, False])) as push_mock:
                    self.bot_it_scheduler.task()
                    compare(1, super_mock.call_count)
                    compare(2, run_mock.call_count)
                    compare(run_mock.mock_calls[0][1][0], "test_bot_1.py")
                    compare(run_mock.mock_calls[1][1][0], "test_bot_2.py")
                    compare(1, push_mock.call_count)
                    compare(push_mock.mock_calls[0][1][0], ["test_bot_1.py"])

    def test_complete_task_no_files_to_process(self):
        with patch("tools.bot_scheduler.BotScheduler.task", mock.Mock()) as super_mock:
            with patch.object(self.bot_it_scheduler, "_run_bot_from_file", mock.Mock(side_effect=[True, False])) as run_mock:
                with patch.object(self.bot_it_scheduler, "_push_files", mock.Mock(side_effect=[True, False])) as push_mock:
                    self.bot_it_scheduler.task()
                    compare(1, super_mock.call_count)
                    compare(0, run_mock.call_count)
                    compare(0, push_mock.call_count)
