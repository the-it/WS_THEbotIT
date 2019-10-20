# pylint: disable=protected-access
import contextlib
import os
import shutil
from pathlib import Path
from unittest import TestCase

from scripts.service.ws_re.register.author import Authors
from scripts.service.ws_re.register.base import _REGISTER_PATH
from scripts.service.ws_re.register.volume import VolumeRegister

_TEST_REGISTER_PATH = Path(__file__).parent.joinpath("test_register")


def copy_tst_data(source: str, destination: str):
    base_path = Path(__file__).parent
    shutil.copy(str(base_path.joinpath("test_data").joinpath(source + ".json")),
                str(base_path.joinpath("test_register").joinpath(destination + ".json")))


def clear_tst_path(renew_path=True):
    with contextlib.suppress(FileNotFoundError):
        shutil.rmtree(_TEST_REGISTER_PATH)
    if renew_path:
        os.mkdir(_TEST_REGISTER_PATH)


class BaseTestRegister(TestCase):
    @classmethod
    def setUpClass(cls):
        clear_tst_path()
        copy_tst_data("authors", "authors")
        copy_tst_data("authors_mapping", "authors_mapping")
        Authors._REGISTER_PATH = _TEST_REGISTER_PATH
        VolumeRegister._REGISTER_PATH = _TEST_REGISTER_PATH

    @classmethod
    def tearDownClass(cls):
        Authors._REGISTER_PATH = _REGISTER_PATH
        VolumeRegister._REGISTER_PATH = _REGISTER_PATH
        clear_tst_path(renew_path=False)
