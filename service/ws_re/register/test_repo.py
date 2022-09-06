# pylint: disable=protected-access,no-self-use
from datetime import datetime, timedelta
from os import path
from pathlib import Path
from unittest import TestCase, mock

from git import Repo
from testfixtures import compare, StringComparison

from service.ws_re.register.repo import DataRepo
from service.ws_re.register.test_base import clear_tst_path
from tools.test import real_wiki_test


class TestDataRepo(TestCase):
    @classmethod
    def setUpClass(cls):
        clear_tst_path()

    @classmethod
    def tearDownClass(cls):
        clear_tst_path(renew_path=False)

    def test_data_path(self):
        compare(Path(__file__).parent.joinpath("data").joinpath("registers"), DataRepo.get_data_path())
        DataRepo.mock_data(True)
        compare(Path(__file__).parent.joinpath("mock_data"), DataRepo.get_data_path())
        DataRepo.mock_data(False)
        compare(Path(__file__).parent.joinpath("data").joinpath("registers"), DataRepo.get_data_path())

    @real_wiki_test
    def test__get_git_repo(self):
        with mock.patch("service.ws_re.register.repo.PATH_REAL_DATA", Path(__file__).parent.joinpath("mock_data")):
            # worst condition path exists but isn't a real git repo
            clear_tst_path(renew_path=True)
            # if git repository doesn't exists it will be freshly cloned from source ... duration more than 1 second
            tick = datetime.now()
            DataRepo._get_git_repo(update_repo=False)
            tock = datetime.now()
            diff = tock - tick  # the result is a datetime.timedelta object
            self.assertTrue(diff > timedelta(seconds=0.1))
            self.assertTrue(path.isfile(Path(__file__)
                                        .parent.joinpath("mock_data").joinpath("registers").joinpath("I_1.json")))
            # further initiations of the git repo will only be initialised locally ... execution time should be quick
            tick = datetime.now()
            for _ in range(10):
                DataRepo._get_git_repo(update_repo=False)
            tock = datetime.now()
            diff = tock - tick  # the result is a datetime.timedelta object
            self.assertTrue(diff < timedelta(seconds=0.1))

    def test_pull(self):
        with mock.patch("service.ws_re.register.repo.Repo", mock.Mock(spec=Repo)) as git_repo_mock:
            DataRepo(update_repo=True)
            compare(3, len(git_repo_mock.mock_calls))
            compare(mock.call().git.reset('--hard'), git_repo_mock.mock_calls[1])
            # last call is the check for diff, after that no more git actions
            compare("().remotes.origin.pull", git_repo_mock.mock_calls[2][0])

    def test_pushing_nothing_to_push(self):
        with mock.patch("service.ws_re.register.repo.Repo", mock.Mock(spec=Repo)) as git_repo_mock:
            git_repo_mock().index.diff.return_value = []
            data_repo = DataRepo()
            data_repo.push()
            compare(3, len(git_repo_mock.mock_calls))
            compare(mock.call(path=Path(__file__).parent.joinpath("data")), git_repo_mock.mock_calls[1])
            # last call is the check for diff, after that no more git actions
            compare("().index.diff", git_repo_mock.mock_calls[2][0])

    def test_pushing_changes(self):
        with mock.patch("service.ws_re.register.repo.Repo", mock.Mock(spec=Repo)) as git_repo_mock:
            git_repo_mock().index.diff.return_value = ["Something has changed"]
            data_repo = DataRepo()
            data_repo.push()
            compare(6, len(git_repo_mock.mock_calls))
            compare(mock.call(path=Path(__file__).parent.joinpath("data")), git_repo_mock.mock_calls[1])
            compare("().index.diff", git_repo_mock.mock_calls[2][0])
            compare("().git.add", git_repo_mock.mock_calls[3][0])
            compare(StringComparison(r".*/service/ws_re/register/data"), git_repo_mock.mock_calls[3][1][0])
            compare("().index.commit", git_repo_mock.mock_calls[4][0])
            compare(StringComparison(r"Updating the register at \d{6}_\d{6}"), git_repo_mock.mock_calls[4][1][0])
            compare("().git.push", git_repo_mock.mock_calls[5][0])

    def test_mock_data(self):
        # nothing should happen during mocked data state
        with mock.patch("service.ws_re.register.repo.Repo", mock.Mock(spec=Repo)) as git_repo_mock:
            DataRepo.mock_data(True)
            data_repo = DataRepo(update_repo=True)
            data_repo.push()
            git_repo_mock.assert_not_called()
            DataRepo.mock_data(False)
