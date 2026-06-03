# pylint: disable=protected-access,no-self-use
from unittest import TestCase

from service.ws_re.register.authors import Authors
from service.ws_re.register.importer import ReImporter
from service.ws_re.register.lemma import Lemma
from service.ws_re.register.registers import Registers
from service.ws_re.register.test_base import BaseTestRegister
from service.ws_re.volumes import Volumes
from tools.test import real_wiki_test


class TestReImporter(TestCase):
    def test_load_tm_list(self):
        tm_set = ReImporter.load_tm_set()
        self.assertTrue("Hermogenes 27" in tm_set)

    @real_wiki_test
    def test_adjust_end_column(self):
        registers = Registers()
        register = registers["XVI,1"]
        for idx, article in enumerate(register):
            if article.lemma == "Molorchos":
                #start test
                pre_1 = """{{REDaten
|BAND=XVI,1
|SPALTE_START=13
|SPALTE_END=OFF
|VORGÄNGER=Molorchia
|NACHFOLGER=Μόλος 1
}}
'''Molorchos'''
[...]
{{REAutor|J. Pley.}}"""
                self.assertTrue("SPALTE_END=14" in ReImporter.adjust_end_column(pre_1, register, idx))
                pre_2 = """{{REDaten
|BAND=XVI,1
|SPALTE_START=12
|SPALTE_END=OFF
|VORGÄNGER=Molorchia
|NACHFOLGER=Μόλος 1
}}
'''Molorchos'''
[...]
{{REAutor|J. Pley.}}"""
                # not clear don't do shit
                self.assertTrue("SPALTE_END=OFF" in ReImporter.adjust_end_column(pre_2, register, idx))
                # index out of range
                self.assertTrue("SPALTE_END=OFF" in ReImporter.adjust_end_column(pre_2, register, 9999))
                pre_3 = """{{REDaten
|BAND=XVI,1
|SPALTE_START=nothing
|SPALTE_END=OFF
|VORGÄNGER=Molorchia
|NACHFOLGER=Μόλος 1
}}
'''Molorchos'''
[...]
{{REAutor|J. Pley.}}"""
                # can't determine start column
                self.assertTrue("SPALTE_END=OFF" in ReImporter.adjust_end_column(pre_3, register, idx))
                pre_4 = """{{REDaten
|BAND=XVI,1
|SPALTE_START=14
|SPALTE_END=OFF
|VORGÄNGER=Molorchia
|NACHFOLGER=Μόλος 1
}}
'''Molorchos'''
[...]
{{REAutor|J. Pley.}}"""
                # start on the same column like follow article
                self.assertTrue("SPALTE_END=OFF" in ReImporter.adjust_end_column(pre_4, register, idx))


class TestGetTextBackup(BaseTestRegister):
    def setUp(self):
        self.authors = Authors()
        self.volume = Volumes()["I,1"]

    def _make_lemma(self, lemma: str, previous: str = None, next_: str = None) -> Lemma:
        lemma_dict = {"lemma": lemma}
        if previous is not None:
            lemma_dict["previous"] = previous
        if next_ is not None:
            lemma_dict["next"] = next_
        return Lemma.from_dict(lemma_dict, self.volume, self.authors)

    def test_uses_article_neighbors_when_set(self):
        article = self._make_lemma("Main", previous="Pre", next_="Post")
        pre = self._make_lemma("OtherPre")
        post = self._make_lemma("OtherPost")
        result = ReImporter.get_text_backup("I,1", article, pre, post)
        self.assertIn("|VORGÄNGER=Pre", result)
        self.assertIn("|NACHFOLGER=Post", result)

    def test_falls_back_to_neighbor_lemma_titles(self):
        article = self._make_lemma("Main")
        pre = self._make_lemma("NeighborPre")
        post = self._make_lemma("NeighborPost")
        result = ReImporter.get_text_backup("I,1", article, pre, post)
        self.assertIn("|VORGÄNGER=NeighborPre", result)
        self.assertIn("|NACHFOLGER=NeighborPost", result)

    def test_empty_when_no_source_and_no_neighbors(self):
        article = self._make_lemma("Main")
        result = ReImporter.get_text_backup("I,1", article)
        self.assertIn("|VORGÄNGER=\n", result)
        self.assertIn("|NACHFOLGER=\n", result)

    def test_mixed_article_and_neighbor(self):
        article = self._make_lemma("Main", previous="Pre")
        post = self._make_lemma("NeighborPost")
        result = ReImporter.get_text_backup("I,1", article, None, post)
        self.assertIn("|VORGÄNGER=Pre", result)
        self.assertIn("|NACHFOLGER=NeighborPost", result)
