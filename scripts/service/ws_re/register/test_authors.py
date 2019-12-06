# pylint: disable=protected-access,no-self-use
from pathlib import Path

from testfixtures import compare

from scripts.service.ws_re.register.authors import Authors
from scripts.service.ws_re.register.test_base import BaseTestRegister


class TestAuthors(BaseTestRegister):
    def test_load_data(self):
        authors = Authors()
        author = authors.get_author_by_mapping("Abbott", "I,1")
        compare("William Abbott", author[0].name)
        compare(None, author[0].death)
        author = authors.get_author_by_mapping("Abel", "I,1")
        compare("Herman Abel", author[0].name)
        compare(1998, author[0].death)
        author = authors.get_author_by_mapping("Abel", "XVI,1")
        compare("Abel", author[0].name)
        compare(1987, author[0].death)
        author = authors.get_author_by_mapping("redirect.", "XVI,1")
        compare("Abert", author[0].name)
        compare(1927, author[0].death)
        author = authors.get_author_by_mapping("redirect_list", "XVI,1")
        compare("Abert", author[0].name)
        compare("Herman Abel", author[1].name)
        compare(1927, author[0].death)
        compare([], authors.get_author_by_mapping("Tada", "XVI,1"))
        author = authors.get_author("Abert|")
        compare("Abert", author.name)

    def test_set_mapping(self):
        authors = Authors()
        compare("William Abbott", authors._mapping["Abbott"])
        self.assertFalse("New" in authors._mapping)
        authors.set_mappings({"William Abbott": "Abbott_new", "New": "New"})
        compare("Abbott_new", authors._mapping["William Abbott"])
        compare("New", authors._mapping["New"])

    def test_set_author(self):
        authors = Authors()

        author = authors.get_author_by_mapping("Abel", "I,1")
        compare("Herman Abel", author[0].name)
        compare(1998, author[0].death)
        compare(None, author[0].birth)
        authors.set_author({"Herman Abel": {"birth": 1900, "death": 1990}})
        author = authors.get_author_by_mapping("Abel", "I,1")
        compare("Herman Abel", author[0].name)
        compare(1990, author[0].death)
        compare(1900, author[0].birth)

        authors.set_author({"Abel2": {"birth": 1950}})
        author = authors._authors["Abel2"]
        compare("Abel2", author.name)
        compare(1950, author.birth)

    def test_persist(self):
        authors = Authors()
        authors.set_mappings({"Foo": "Bar"})
        authors.set_author({"Foo Bar": {"birth": 1234}})
        authors.persist()
        base_path = Path(__file__).parent.joinpath("test_register")
        with open(str(base_path.joinpath("authors_mapping.json")), mode="r", encoding="utf8") as mapping:
            compare(True, "\"Foo\": \"Bar\"" in mapping.read())
        with open(str(base_path.joinpath("authors.json")), mode="r", encoding="utf8") as authors:
            compare(True, "  \"Foo Bar\": {\n    \"birth\": 1234\n  }" in authors.read())

    def test_iter(self):
        authors = iter(Authors())
        compare("Herman Abel", next(authors).name)
        compare("Abel", next(authors).name)
        compare("Abert", next(authors).name)
        compare("William Abbott", next(authors).name)
        with self.assertRaises(StopIteration):
            # redirects doesn't count
            next(authors)
