# pylint: disable=no-self-use,protected-access
from collections import OrderedDict

from testfixtures import compare

from scripts.service.ws_re.register.authors import Authors
from scripts.service.ws_re.register.lemma import Lemma
from scripts.service.ws_re.register.test_base import BaseTestRegister, copy_tst_data
from scripts.service.ws_re.register.register_types.alphabetic import AlphabeticRegister
from scripts.service.ws_re.register.register_types.volume import VolumeRegister
from scripts.service.ws_re.volumes import Volumes


class TestAlphabeticRegister(BaseTestRegister):
    def setUp(self):
        copy_tst_data("I_1_alpha", "I_1")
        copy_tst_data("III_1_alpha", "III_1")
        self.authors = Authors()
        self.volumes = Volumes()
        self.registers = OrderedDict()
        self.registers["I,1"] = VolumeRegister(self.volumes["I,1"], self.authors)
        self.registers["III,1"] = VolumeRegister(self.volumes["III,1"], self.authors)

    def test_init(self):
        a_register = AlphabeticRegister("a", "be", None, "zzzzzz", self.registers)
        b_register = AlphabeticRegister("be", "zzzzzz", "a", None, self.registers)
        compare(5, len(a_register))
        compare(5, len(b_register))
        compare("Aal", a_register[0]["lemma"])
        compare("Baaba", a_register[4]["lemma"])
        compare("Beta", b_register[0]["lemma"])
        compare("Vaaa", b_register[4]["lemma"])
        compare("Ueee", b_register[5]["lemma"])

    def test_squash_lemmas(self):
        register = AlphabeticRegister("a", "be", None, "zzzzzz", OrderedDict())
        lemma1 = Lemma({"lemma": "lemma", "chapters": [{"start": 1, "end": 1, "author": "Abel"}]},
                       Volumes()["I,1"],
                       self.authors)
        lemma2 = Lemma({"lemma": "lemma", "chapters": [{"start": 1, "end": 1, "author": "Abel"}]},
                       Volumes()["III,1"],
                       self.authors)
        lemma3 = Lemma({"lemma": "lemma2", "chapters": [{"start": 1, "end": 1, "author": "Abel"}]},
                       Volumes()["III,1"],
                       self.authors)
        lemmas = [lemma1, lemma2, lemma3]
        expection = [[lemma1, lemma2], [lemma3]]
        compare(expection, register.squash_lemmas(lemmas))

    def test_squash_lemmas_empty(self):
        register = AlphabeticRegister("a", "be", None, None, OrderedDict())
        expection = []
        compare(expection, register.squash_lemmas([]))

    def test_make_header(self):
        a_register = AlphabeticRegister("a", "be", None, "c", self.registers)
        b_register = AlphabeticRegister("be", "c", "a", "zzzzzz", self.registers)
        c_register = AlphabeticRegister("c", "zzzzzz", "be", None, self.registers)
        expected_header = """{{RERegister
|ALPHABET=a
|NF=be
|NFNF=c
|SUM=5
|UNK=2
|KOR=1
|FER=1
}}
"""
        compare(expected_header, a_register._get_header())
        expected_header = """{{RERegister
|ALPHABET=be
|VG=a
|NF=c
|NFNF=zzzzzz
|SUM=2
|UNK=1
|KOR=0
|FER=1
}}
"""
        compare(expected_header, b_register._get_header())
        expected_header = """{{RERegister
|ALPHABET=c
|VG=be
|NF=zzzzzz
|SUM=4
|UNK=0
|KOR=1
|FER=2
}}
"""
        compare(expected_header, c_register._get_header())

    def test_make_table(self):
        b_register = AlphabeticRegister("be", "zzzzzz", "a", None, self.registers)
        expected_table = """{{RERegister
|ALPHABET=be
|VG=a
|NF=zzzzzz
|SUM=6
|UNK=1
|KOR=1
|FER=3
}}

{|class="wikitable sortable"
!Artikel
!Band
!Wikilinks
!Seite
!Autor
!Sterbejahr
|-
|rowspan=3 data-sort-value="beta"|[[RE:Beta|'''{{Anker2|Beta}}''']]
|rowspan=2 |I,1
|rowspan=2 |
|[[Special:Filepath/Pauly-Wissowa_I,1,_0003.jpg|4]]
|Abert
|style="background:#B9FFC5"|1927
|-
|[[Special:Filepath/Pauly-Wissowa_I,1,_0003.jpg|4]]-5
|Herman Abel
|style="background:#FFCBCB"|1998
|-
||III,1
||
|-
|data-sort-value="charlie"|[[RE:Charlie|'''{{Anker2|Charlie}}''']]
||III,1
||
|[[Special:Filepath/Pauly-Wissowa_III,1,_0003.jpg|4]]
|Herman Abel
|style="background:#FFCBCB"|1998
|-
|data-sort-value="delta"|[[RE:Delta|'''{{Anker2|Delta}}''']]
||III,1
||
|[[Special:Filepath/Pauly-Wissowa_III,1,_0003.jpg|4]]
|Abert
|style="background:#B9FFC5"|1927
|-
|data-sort-value="uaaa"|[[RE:Vaaa|'''{{Anker2|Vaaa}}''']]
||III,1
||
|[[Special:Filepath/Pauly-Wissowa_III,1,_0003.jpg|4]]
|Abert
|style="background:#B9FFC5"|1927
|-
|data-sort-value="ueee"|[[RE:Ueee|'''{{Anker2|Ueee}}''']]
||III,1
||
|[[Special:Filepath/Pauly-Wissowa_III,1,_0003.jpg|4]]
|Abert
|style="background:#B9FFC5"|1927
|}
[[Kategorie:RE:Register|!]]
Zahl der Artikel: 6, """
        compare(expected_table, b_register.get_register_str())
