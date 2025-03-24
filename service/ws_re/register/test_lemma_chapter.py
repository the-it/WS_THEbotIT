# pylint: disable=no-self-use,protected-access
from collections import OrderedDict
from unittest.case import TestCase

from responses import start
from testfixtures import compare

from service.ws_re.register.lemma_chapter import LemmaChapter


class TestLemmaChapter(TestCase):
    def test_no_author(self):
        lemma_chapter = LemmaChapter.from_dict({"start": 1, "end": 2})
        compare(None, lemma_chapter.author)

    def test_return_dict(self):
        lemma_chapter = LemmaChapter(start= 1, end=2, author="bla")
        compare(OrderedDict((("start", 1), ("end", 2), ("author", "bla"))), lemma_chapter.to_dict())
