# pylint: disable=protected-access,no-self-use
import json
from pathlib import Path

from testfixtures import compare

from scripts.service.ws_re.register.clean import CleanAuthors
from scripts.service.ws_re.register.test_base import BaseTestRegister, _TEST_REGISTER_PATH, \
    copy_tst_data

BASE_PATH: Path = Path(__file__).parent

class TestCleanAuthors(BaseTestRegister):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        copy_tst_data("authors_clean", "authors")
        copy_tst_data("authors_mapping_clean", "authors_mapping")

    def test_clean_authors(self):
        cleaner = CleanAuthors()
        cleaner.delete_authors_without_mapping()
        with open(BASE_PATH.joinpath("test_data/authors_clean_expection.json")) as expection_file, \
                open(_TEST_REGISTER_PATH.joinpath("authors.json")) as cleaned_file:
            compare(json.load(expection_file), json.load(cleaned_file))
