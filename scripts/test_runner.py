import os
import time
from datetime import datetime
from pathlib import Path
from shutil import rmtree, copy
from unittest import TestCase, mock, skip

from git import Repo
from testfixtures import StringComparison, compare

from scripts.runner import TheBotItScheduler


class TestBotScheduler(TestCase):
    def _get_path_for_scripts(self) -> Path:
        repo_root = Path(__file__).parent.parent
        scripts = repo_root.joinpath("scripts")
        self.assertTrue(os.path.isdir(scripts))
        return scripts

    def _get_archive_test(self) -> Path:
        return self._get_path_for_scripts().joinpath("archive_test")\
            .joinpath(str(datetime.today().year))

    def _get_one_time_run_test(self) -> Path:
        return self._get_path_for_scripts().joinpath("one_time_run_test")

    @staticmethod
    def _create_dir_and_init(path: Path):
        os.makedirs(path)
        open(path.joinpath("__init__.py"), 'w').close()

    def _copy_bot_to_run_dir(self, name: str):
        copy(Path(__file__).parent.joinpath("test_bots_for_scheduler", "{}.py".format(name)),
             self._get_one_time_run_test())
        time.sleep(0.1)

    def _copy_bot_to_archive_dir(self, name: str):
        copy(Path(__file__).parent.joinpath("test_bots_for_scheduler", "{}.py".format(name)),
             self._get_archive_test())

    def _remove_temp_folder(self):
        if os.path.exists(self._get_path_for_scripts().joinpath("archive_test")):
            rmtree(self._get_path_for_scripts().joinpath("archive_test"))
        if os.path.exists(self._get_one_time_run_test()):
            rmtree(self._get_one_time_run_test())

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
        self._copy_bot_to_run_dir("bot_1")
        os.mkdir(self._get_one_time_run_test().joinpath("some_folder"))
        open(self._get_one_time_run_test().joinpath("bot_1_test.py"), 'w').close()
        with open(self._get_one_time_run_test().joinpath("bot_1_test.py"), 'w') as file_pointer:
            file_pointer.write("import something_not_exist\n\nprint(\"blub\")")
        self._copy_bot_to_run_dir("bot_2")
        os.mkdir(self._get_one_time_run_test().joinpath("testfolder"))
        file_list = self.bot_it_scheduler._get_files_to_run()
        compare(2, len(file_list))
        self.assertIn("bot_1.py", file_list)
        self.assertIn("bot_2.py", file_list)

    def test_run_one_bot_from_file(self):
        self._copy_bot_to_run_dir("bot_1")
        with open(self._get_one_time_run_test().joinpath("bot_1_test.py"), 'w') as file_pointer:
            file_pointer.write("import something_not_exist\n\nprint(\"blub\")")
        with mock.patch.object(self.bot_it_scheduler, "run_bot", mock.Mock(return_value=True)) as run_mock:
            self.assertTrue(self.bot_it_scheduler._run_bot_from_file("bot_1.py"))
            compare(1, run_mock.call_count)
            compare(type(run_mock.mock_calls[0][1][0]).__name__, "TestBot1")

    @skip("I don't know what is wrong here ... but sometimes the system is unable to find this file.")
    def test_run_two_bots_from_file(self):
        self._copy_bot_to_run_dir("bot_34")
        # both runs successfule
        with mock.patch.object(self.bot_it_scheduler, "run_bot", mock.Mock(return_value=True)) as run_mock:
            self.assertTrue(self.bot_it_scheduler._run_bot_from_file("bot_34.py"))
            compare(2, run_mock.call_count)
            compare(type(run_mock.mock_calls[0][1][0]).__name__, "TestBot3")
            compare(type(run_mock.mock_calls[1][1][0]).__name__, "TestBot4")
        # second run with errors
        with mock.patch.object(self.bot_it_scheduler, "run_bot", mock.Mock(side_effect=[True, False])) as run_mock:
            self.assertFalse(self.bot_it_scheduler._run_bot_from_file("bot_34.py"))
            compare(2, run_mock.call_count)
            compare(type(run_mock.mock_calls[0][1][0]).__name__, "TestBot3")
            compare(type(run_mock.mock_calls[1][1][0]).__name__, "TestBot4")
        # first run with errors
        with mock.patch.object(self.bot_it_scheduler, "run_bot", mock.Mock(side_effect=[False, True])) as run_mock:
            self.assertFalse(self.bot_it_scheduler._run_bot_from_file("bot_34.py"))
            compare(2, run_mock.call_count)
            compare(type(run_mock.mock_calls[0][1][0]).__name__, "TestBot3")
            compare(type(run_mock.mock_calls[1][1][0]).__name__, "TestBot4")

    def test_move_file_folder_exists(self):
        self._copy_bot_to_run_dir("bot_1")
        now = datetime.today()
        path_to_current_archive = self._get_archive_test()
        self.bot_it_scheduler._move_file_to_archive("bot_1.py")
        self.assertIn("bot_1.py", os.listdir(path_to_current_archive))
        with open(path_to_current_archive.joinpath("bot_1.py"), "r") as bot_file:
            compare(StringComparison("# successful processed on {}".format(now.strftime("%Y-%m-%d"))), bot_file.readline())

    def test_move_file_with_test(self):
        self._copy_bot_to_run_dir("bot_1")
        open(self._get_one_time_run_test().joinpath("bot_1_test.py"), 'w').close()
        open(self._get_one_time_run_test().joinpath("bot_1_test_data.txt"), 'w').close()
        now = datetime.today()
        path_to_current_archive = self._get_archive_test()
        self.bot_it_scheduler._move_file_to_archive("bot_1.py")
        self.assertIn("bot_1.py", os.listdir(path_to_current_archive))
        with open(path_to_current_archive.joinpath("bot_1.py"), "r") as bot_file:
            compare(StringComparison("# successful processed on {}".format(now.strftime("%Y-%m-%d"))), bot_file.readline())
        self.assertTrue(os.path.exists(path_to_current_archive.joinpath("bot_1.py")))
        self.assertTrue(os.path.exists(path_to_current_archive.joinpath("bot_1_test_data.txt")))

    def test_move_file_folder_not_exists(self):
        self._copy_bot_to_run_dir("bot_1")
        path_to_current_archive = self._get_archive_test()
        # os.mkdir(path_to_current_archive), don't create the folder
        self.bot_it_scheduler._move_file_to_archive("bot_1.py")
        self.assertIn("bot_1.py", os.listdir(path_to_current_archive))
        self.assertIn("__init__.py", os.listdir(path_to_current_archive))

    def test_change_repo(self):
        self._copy_bot_to_archive_dir("bot_1")
        with mock.patch("scripts.runner.git.Repo", mock.Mock(spec=Repo)) as repo_mock:
            self.bot_it_scheduler._push_files(["bot_1.py"])
            file_add = [self._get_archive_test().joinpath("bot_1.py")]
            file_remove = [self._get_one_time_run_test().joinpath("bot_1.py")]
            compare(mock.call(search_parent_directories=True), repo_mock.mock_calls[0])
            compare("().index.add", repo_mock.mock_calls[1][0])
            compare(file_add, repo_mock.mock_calls[1][1][0])
            compare("().index.remove", repo_mock.mock_calls[2][0])
            compare(file_remove, repo_mock.mock_calls[2][1][0])
            compare("().index.commit", repo_mock.mock_calls[3][0])
            compare("move successful bot scripts: bot_1.py", repo_mock.mock_calls[3][1][0])
            compare("().remote", repo_mock.mock_calls[4][0])
            compare("origin", repo_mock.mock_calls[4][1][0])
            compare("().remote().push", repo_mock.mock_calls[5][0])

    def test_change_repo_two_bots(self):
        self._copy_bot_to_archive_dir("bot_1")
        open(self._get_archive_test().joinpath("bot_1_test.py"), 'w').close()
        self._copy_bot_to_archive_dir("bot_2")
        with mock.patch("scripts.runner.git.Repo", mock.Mock(spec=Repo)) as repo_mock:
            self.bot_it_scheduler._push_files(["bot_1.py", "bot_2.py"])
            file_add = [self._get_archive_test().joinpath("bot_1.py"),
                        self._get_archive_test().joinpath("bot_1_test.py"),
                        self._get_archive_test().joinpath("bot_2.py")]
            file_remove = [self._get_one_time_run_test().joinpath("bot_1.py"),
                           self._get_one_time_run_test().joinpath("bot_1_test.py"),
                           self._get_one_time_run_test().joinpath("bot_2.py")]
            compare(mock.call(search_parent_directories=True), repo_mock.mock_calls[0])
            compare("().index.add", repo_mock.mock_calls[1][0])
            compare(set(file_add), set(repo_mock.mock_calls[1][1][0]))
            compare("().index.remove", repo_mock.mock_calls[2][0])
            compare(set(file_remove), set(repo_mock.mock_calls[2][1][0]))
            compare("().index.commit", repo_mock.mock_calls[3][0])
            compare("move successful bot scripts: bot_1.py, bot_2.py", repo_mock.mock_calls[3][1][0])
            compare("().remote", repo_mock.mock_calls[4][0])
            compare("origin", repo_mock.mock_calls[4][1][0])
            compare("().remote().push", repo_mock.mock_calls[5][0])

    def test_complete_task(self):
        self._copy_bot_to_run_dir("bot_1")
        with open(self._get_one_time_run_test().joinpath("bot_1_test.py"), 'w') as file_pointer:
            file_pointer.write("import something_not_exist\n\nprint(\"blub\")")
        self._copy_bot_to_run_dir("bot_2")
        with mock.patch("tools.bot_scheduler.BotScheduler.task", mock.Mock()) as super_mock:
            with mock.patch.object(self.bot_it_scheduler, "_run_bot_from_file", mock.Mock(side_effect=[True, False])) as run_mock:
                with mock.patch.object(self.bot_it_scheduler, "_push_files", mock.Mock(side_effect=[True, False])) as push_mock:
                    self.bot_it_scheduler.task()
                    compare(1, super_mock.call_count)
                    compare(2, run_mock.call_count)
                    compare(run_mock.mock_calls[0][1][0], "bot_1.py")
                    compare(run_mock.mock_calls[1][1][0], "bot_2.py")
                    compare(1, push_mock.call_count)
                    compare(push_mock.mock_calls[0][1][0], ["bot_1.py"])

    def test_complete_task_no_files_to_process(self):
        with mock.patch("tools.bot_scheduler.BotScheduler.task", mock.Mock()) as super_mock:
            with mock.patch.object(self.bot_it_scheduler, "_run_bot_from_file", mock.Mock(side_effect=[True, False])) as run_mock:
                with mock.patch.object(self.bot_it_scheduler, "_push_files", mock.Mock(side_effect=[True, False])) as push_mock:
                    self.bot_it_scheduler.task()
                    compare(1, super_mock.call_count)
                    compare(0, run_mock.call_count)
                    compare(0, push_mock.call_count)
