# pylint: disable=protected-access
import contextlib
import os
import shutil
from pathlib import Path
from unittest import TestCase

from service.ws_re.register.repo import DataRepo

PATH_MOCK_DATA = Path(__file__).parent.joinpath("mock_data")

def copy_tst_data(source: str, destination: str):
    base_path = Path(__file__).parent
    shutil.copy(str(base_path.joinpath("test_data/register_stubs").joinpath(source + ".json")),
                str(PATH_MOCK_DATA.joinpath(destination + ".json")))


def clear_tst_path(renew_path=True):
    with contextlib.suppress(FileNotFoundError):
        shutil.rmtree(PATH_MOCK_DATA)
    if renew_path:
        os.mkdir(PATH_MOCK_DATA)


class BaseTestRegister(TestCase):
    @classmethod
    def setUpClass(cls):
        DataRepo.mock_data(True)
        clear_tst_path()
        copy_tst_data("authors", "authors")
        copy_tst_data("authors_mapping", "authors_mapping")

    @classmethod
    def tearDownClass(cls):
        clear_tst_path(renew_path=False)
        DataRepo.mock_data(False)
