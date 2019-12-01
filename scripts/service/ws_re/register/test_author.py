# pylint: disable=protected-access,no-self-use
from unittest import TestCase

from testfixtures import compare

from scripts.service.ws_re.register.author import Author


class TestAuthor(TestCase):
    def test_author(self):
        register_author = Author("Test Name", {"death": 1999})
        compare("Test Name", register_author.name)
        compare(1999, register_author.death)
        compare(None, register_author.birth)

        register_author = Author("Test Name", {"birth": 1999})
        compare(None, register_author.death)
        compare(1999, register_author.birth)

        register_author = Author("Test Name", {"first_name": "Test"})
        compare("Test", register_author.first_name)

        register_author = Author("Test Name", {"last_name": "Name"})
        compare("Name", register_author.last_name)

        register_author = Author("Test Name", {"redirect": "Tada"})
        compare(None, register_author.death)
        compare("Tada", register_author.redirect)
