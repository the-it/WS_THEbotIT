# pylint: disable=no-self-use,protected-access
from collections import OrderedDict
from unittest.case import TestCase

from testfixtures import compare

from service.ws_re.register.lemma_chapter import LemmaChapter


class TestLemmaChapter(TestCase):
    def test_error_in_is_valid(self):
        lemma_chapter = LemmaChapter(1)
        compare(False, lemma_chapter.is_valid())
        lemma_chapter = LemmaChapter({"end": 2})
        compare(False, lemma_chapter.is_valid())
        lemma_chapter = LemmaChapter({"start": 2})
        compare(False, lemma_chapter.is_valid())
        lemma_chapter = LemmaChapter({"start": 1, "end": 2})
        compare(True, lemma_chapter.is_valid())

    def test_no_author(self):
        lemma_chapter = LemmaChapter({"start": 1, "end": 2})
        compare(None, lemma_chapter.author)

    def test_return_dict(self):
        lemma_chapter = LemmaChapter({"author": "bla", "end": 2, "start": 1})
        compare(OrderedDict((("start", 1), ("end", 2), ("author", "bla"))), lemma_chapter.get_dict())
