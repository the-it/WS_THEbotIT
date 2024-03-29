# pylint: disable=protected-access,no-self-use
import json
from pathlib import Path

from testfixtures import compare

from service.ws_re.register.clean import CleanAuthors
from service.ws_re.register.repo import DataRepo
from service.ws_re.register.test_base import BaseTestRegister, copy_tst_data

BASE_PATH: Path = Path(__file__).parent

class TestCleanAuthors(BaseTestRegister):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        copy_tst_data("authors_clean", "authors")
        copy_tst_data("authors_mapping_clean", "authors_mapping")
        copy_tst_data("I_1_clean", "I_1")

    def test_clean_authors(self):
        cleaner = CleanAuthors()
        cleaner.delete_authors_without_mapping()
        with open(BASE_PATH.joinpath("test_data/register_stubs/authors_clean_expection.json"), encoding="utf-8") \
                as expection_file:
            with open(DataRepo.get_data_path().joinpath("authors.json"), encoding="utf-8") as cleaned_file:
                compare(json.load(expection_file), json.load(cleaned_file))

    def test_clean_mapping(self):
        cleaner = CleanAuthors()
        cleaner.delete_mappings_without_use()
        with open(BASE_PATH.joinpath(
                "test_data/register_stubs/authors_mapping_clean_expection.json"), encoding="utf-8") \
                as expection_file, \
                open(DataRepo.get_data_path().joinpath("authors_mapping.json"), encoding="utf-8") as cleaned_file:
            compare(json.load(expection_file), json.load(cleaned_file))


class TestRemapAuthors(BaseTestRegister):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        copy_tst_data("authors_remap", "authors")
        copy_tst_data("authors_mapping_remap", "authors_mapping")

    def test_remap(self):
        cleaner = CleanAuthors()
        cleaner.remap()
        with open(BASE_PATH.joinpath(
                "test_data/register_stubs/authors_mapping_remap_expection.json"), encoding="utf-8") \
                as expection_file, \
                open(DataRepo.get_data_path().joinpath("authors_mapping.json"), encoding="utf-8") as cleaned_file:
            compare(json.load(expection_file), json.load(cleaned_file))
