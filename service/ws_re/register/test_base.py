# pylint: disable=protected-access
import contextlib
import os
import shutil
from pathlib import Path
from unittest import TestCase, mock

from service.ws_re.register.authors import Authors
from service.ws_re.register.register_types.volume import VolumeRegister

_TEST_REGISTER_PATH = Path(__file__).parent.joinpath("mock_data")


def copy_tst_data(source: str, destination: str):
    base_path = Path(__file__).parent
    shutil.copy(str(base_path.joinpath("test_data/register_stubs").joinpath(source + ".json")),
                str(_TEST_REGISTER_PATH.joinpath(destination + ".json")))


def clear_tst_path(renew_path=True):
    with contextlib.suppress(FileNotFoundError):
        shutil.rmtree(_TEST_REGISTER_PATH)
    if renew_path:
        os.mkdir(_TEST_REGISTER_PATH)


class BaseTestRegister(TestCase):
    @classmethod
    def setUpClass(cls):
        mock_data_mock = mock.patch("service.ws_re.register.repo.MOCK_DATA", mock.Mock).start()
        mock_data_mock.return_value = True
        clear_tst_path()
        copy_tst_data("authors", "authors")
        copy_tst_data("authors_mapping", "authors_mapping")
        Authors._REGISTER_PATH = _TEST_REGISTER_PATH
        VolumeRegister._REGISTER_PATH = _TEST_REGISTER_PATH

    @classmethod
    def tearDownClass(cls):
        clear_tst_path(renew_path=False)
        mock.patch.stopall()
