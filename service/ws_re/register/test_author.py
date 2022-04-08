# pylint: disable=protected-access,no-self-use
from unittest import TestCase

from testfixtures import compare

from service.ws_re.register.author import Author


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

        register_author = Author("Test Name", {"ws_lemma": "Tada_lemma"})
        compare(None, register_author.death)
        compare("Tada_lemma", register_author.ws_lemma)

        register_author = Author("Test Name", {"wp_lemma": "Tada_lemma"})
        compare(None, register_author.death)
        compare("Tada_lemma", register_author.wp_lemma)

    def testPublicDomain(self):
        author = Author("Test Name", {})
        compare(2100, author.year_public_domain)

        author = Author("Test Name", {"death": 1900})
        compare(1971, author.year_public_domain)

        author = Author("Test Name", {"birth": 1900})
        compare(2051, author.year_public_domain)

        author = Author("Test Name", {"death": 1950, "birth": 1900})
        compare(2021, author.year_public_domain)
