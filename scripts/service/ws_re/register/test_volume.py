from unittest import TestCase, skip

from testfixtures import compare

from scripts.service.ws_re.register.author import Authors
from scripts.service.ws_re.register.test_base import BaseTestRegister, copy_tst_data, \
    _TEST_REGISTER_PATH
from scripts.service.ws_re.register.volume import VolumeRegister
from scripts.service.ws_re.volumes import Volumes


class TestRegister(BaseTestRegister):
    def test_init(self):
        copy_tst_data("I_1_base", "I_1")
        VolumeRegister(Volumes()["I,1"], Authors())

    def test_header_band(self):
        copy_tst_data("I_1_base", "I_1")
        self.assertTrue("BAND=I,1" in VolumeRegister(Volumes()["I,1"], Authors())._get_header())
        copy_tst_data("I_1_base", "S I")
        self.assertTrue("BAND=S I" in VolumeRegister(Volumes()["S I"], Authors())._get_header())

    def test_get_table(self):
        copy_tst_data("I_1_two_entries", "I_1")
        register = VolumeRegister(Volumes()["I,1"], Authors())
        expected_table = """{{RERegister
|BAND=I,1
|ALPHABET=
|AUTHOR=
|VG=
|NF=I,2
|NFNF=
|SUM=2
|UNK=0
|KOR=1
|FER=1
}}

{|class="wikitable sortable"
!Artikel
!Wikilinks
!Seite
!Autor
!Sterbejahr
|-
|data-sort-value="aal"|[[RE:Aal|'''{{Anker2|Aal}}''']]
||
|[[Special:Filepath/Pauly-Wissowa_I,1,_0001.jpg|1]]-4
|Abel
|style="background:#FFCBCB"|1998
|-
|data-sort-value="aarassos"|[[RE:Aarassos|'''{{Anker2|Aarassos}}''']]
||
|[[Special:Filepath/Pauly-Wissowa_I,1,_0003.jpg|4]]
|Abert
|style="background:#B9FFC5"|1927
|}
[[Kategorie:RE:Register|!]]
Zahl der Artikel: 2, davon [[:Kategorie:RE:Band I,1|{{PAGESINCATEGORY:RE:Band I,1|pages}} in Volltext]]."""
        compare(expected_table, register.get_register_str())

    def test_persist(self):
        copy_tst_data("I_1_two_entries", "I_1")
        register = VolumeRegister(Volumes()["I,1"], Authors())
        register._lemmas[0]._lemma_dict["previous"] = None
        register._lemmas[0]._chapters[0]._dict["author"] = "ÄäÖöÜüß"
        register.persist()
        expect = """[
  {
    "lemma": "Aal",
    "next": "Aarassos",
    "proof_read": 3,
    "chapters": [
      {
        "start": 1,
        "end": 4,
        "author": "ÄäÖöÜüß"
      }
    ]
  },
  {
    "lemma": "Aarassos",
    "previous": "Aal",
    "proof_read": 2,
    "chapters": [
      {
        "start": 4,
        "end": 4,
        "author": "Abert"
      }
    ]
  }
]"""
        with open(_TEST_REGISTER_PATH.joinpath("I_1.json"), mode="r", encoding="utf-8") as register_file:
            compare(expect, register_file.read())

    def test_normalize_sort_key(self):
        compare("aaa", VolumeRegister.normalize_sort_key({"lemma": "ååå"}))
        compare("bbb", VolumeRegister.normalize_sort_key({"lemma": "ååå", "sort_key": "bbb"}))

    def test_get_lemma_by_name(self):
        copy_tst_data("I_1_base", "I_1")
        register = VolumeRegister(Volumes()["I,1"], Authors())
        lemma = register.get_lemma_by_name("Aba 1")
        compare("Aarassos", lemma["previous"])
        self.assertIsNone(register.get_lemma_by_name("Abracadabra"))

    def test_get_lemma_by_sort_key(self):
        copy_tst_data("I_1_base", "I_1")
        register = VolumeRegister(Volumes()["I,1"], Authors())
        lemma = register.get_lemma_by_sort_key("äbÄ 1")
        compare("Aarassos", lemma["previous"])
        self.assertIsNone(register.get_lemma_by_name("Abracadabra"))

    def test_get_lemma_self_append(self):
        copy_tst_data("I_1_self_append", "I_1")
        register = VolumeRegister(Volumes()["I,1"], Authors())
        lemma = register.get_lemma_by_name("Aal")
        compare(None, lemma["previous"])
        lemma = register.get_lemma_by_name("Aal", self_supplement=True)
        compare("Something", lemma["previous"])
        lemma = register.get_lemma_by_sort_key("AAL", self_supplement=True)
        compare("Something", lemma["previous"])
        lemma = register.get_lemma_by_name("Something", self_supplement=True)
        compare(None, lemma)

    def test_get_lemma_by_id(self):
        copy_tst_data("I_1_base", "I_1")
        register = VolumeRegister(Volumes()["I,1"], Authors())
        lemma = register[2]
        compare("Aarassos", lemma["previous"])
        with self.assertRaises(IndexError):
            register[8]

    def test_get_id_of_lemma(self):
        copy_tst_data("I_1_self_append", "I_1")
        register = VolumeRegister(Volumes()["I,1"], Authors())
        compare(0, register.get_index_of_lemma("Aal"))
        compare(2, register.get_index_of_lemma("Something"))
        compare(3, register.get_index_of_lemma("Aal", self_supplement=True))
        lemma = register.get_lemma_by_name("Aal", self_supplement=True)
        compare(3, register.get_index_of_lemma(lemma))
        compare(None, register.get_index_of_lemma("Lemma not there"))


@skip("only for analysis")
class TestIntegrationRegister(TestCase):
    def test_json_integrity(self):  # pragma: no cover
        for volume in Volumes().all_volumes:
            print(volume)
            VolumeRegister(volume, Authors)
