# pylint: disable=protected-access,no-self-use
from datetime import datetime
from pathlib import Path
from unittest import TestCase, mock

from git import GitError, Repo
from testfixtures import StringComparison, compare

from service.ws_re.register.repo import REPO_URL, DataRepo
from service.ws_re.register.test_base import clear_tst_path


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

    def test__get_git_repo_clone_if_no_repo(self):
        data_path = Path(__file__).parent.joinpath("mock_data")
        with (
            mock.patch("service.ws_re.register.repo.PATH_REAL_DATA", data_path),
            mock.patch("service.ws_re.register.repo.Repo", mock.Mock(spec=Repo)) as git_repo_mock,
            mock.patch("service.ws_re.register.repo.shutil.rmtree") as rmtree_mock,
        ):
            # path exists but isn't a real git repo
            git_repo_mock.side_effect = GitError("no repo")
            git_repo_mock.clone_from.return_value = "cloned repo"
            compare("cloned repo", DataRepo._get_git_repo(update_repo=False))
            rmtree_mock.assert_called_once_with(data_path)
            git_repo_mock.clone_from.assert_called_once_with(url=REPO_URL, to_path=data_path)

    def test__get_git_repo_existing_repo_is_not_cloned(self):
        data_path = Path(__file__).parent.joinpath("mock_data")
        with (
            mock.patch("service.ws_re.register.repo.PATH_REAL_DATA", data_path),
            mock.patch("service.ws_re.register.repo.Repo", mock.Mock(spec=Repo)) as git_repo_mock,
        ):
            for _ in range(10):
                compare(git_repo_mock.return_value, DataRepo._get_git_repo(update_repo=False))
            compare(10, git_repo_mock.call_count)
            git_repo_mock.assert_called_with(path=data_path)
            git_repo_mock.clone_from.assert_not_called()

    def test_pull(self):
        with mock.patch("service.ws_re.register.repo.Repo", mock.Mock(spec=Repo)) as git_repo_mock:
            DataRepo(update_repo=True)
            compare(3, len(git_repo_mock.mock_calls))
            compare(mock.call().git.reset("--hard"), git_repo_mock.mock_calls[1])
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

    def test_checkout_commit_after(self):
        with mock.patch("service.ws_re.register.repo.Repo", mock.Mock(spec=Repo)) as git_repo_mock:
            commit_old = mock.Mock(hexsha="aaa", committed_datetime=datetime(2024, 1, 1))
            commit_mid = mock.Mock(hexsha="bbb", committed_datetime=datetime(2024, 6, 1))
            commit_new = mock.Mock(hexsha="ccc", committed_datetime=datetime(2024, 12, 1))
            git_repo_mock().iter_commits.return_value = iter([commit_old, commit_mid, commit_new])
            data_repo = DataRepo()
            data_repo.checkout_commit_after(datetime(2024, 3, 1))
            git_repo_mock().iter_commits.assert_called_with(reverse=True)
            git_repo_mock().git.checkout.assert_called_once_with("bbb")

    def test_checkout_commit_after_no_match(self):
        with mock.patch("service.ws_re.register.repo.Repo", mock.Mock(spec=Repo)) as git_repo_mock:
            commit_old = mock.Mock(hexsha="aaa", committed_datetime=datetime(2024, 1, 1))
            git_repo_mock().iter_commits.return_value = iter([commit_old])
            data_repo = DataRepo()
            data_repo.checkout_commit_after(datetime(2025, 1, 1))
            git_repo_mock().git.checkout.assert_not_called()

    def test_checkout_commit_after_mocked_data(self):
        with mock.patch("service.ws_re.register.repo.Repo", mock.Mock(spec=Repo)) as git_repo_mock:
            DataRepo.mock_data(True)
            data_repo = DataRepo()
            data_repo.checkout_commit_after(datetime(2024, 1, 1))
            git_repo_mock.assert_not_called()
            DataRepo.mock_data(False)

    def test_mock_data(self):
        # nothing should happen during mocked data state
        with mock.patch("service.ws_re.register.repo.Repo", mock.Mock(spec=Repo)) as git_repo_mock:
            DataRepo.mock_data(True)
            data_repo = DataRepo(update_repo=True)
            data_repo.push()
            git_repo_mock.assert_not_called()
            DataRepo.mock_data(False)
