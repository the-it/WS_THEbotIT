from collections import OrderedDict

from testfixtures import compare

from scripts.service.ws_re.register.alphabetic import AlphabeticRegister
from scripts.service.ws_re.register.author import Authors
from scripts.service.ws_re.register.lemma import Lemma
from scripts.service.ws_re.register.test_base import BaseTestRegister, copy_tst_data
from scripts.service.ws_re.register.volume import VolumeRegister
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
        a_register = AlphabeticRegister("a", "be", self.registers)
        b_register = AlphabeticRegister("be", "zzzzzz", self.registers)
        compare(5, len(a_register))
        compare(5, len(b_register))
        compare("Aal", a_register[0]["lemma"])
        compare("Baaba", a_register[4]["lemma"])
        compare("Beta", b_register[0]["lemma"])
        compare("Vaaa", b_register[4]["lemma"])
        compare("Ueee", b_register[5]["lemma"])

    def test_squash_lemmas(self):
        register = AlphabeticRegister("a", "be", OrderedDict())
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
        register = AlphabeticRegister("a", "be", OrderedDict())
        expection = []
        compare(expection, register.squash_lemmas([]))

    def test_make_table(self):
        b_register = AlphabeticRegister("be", "zzzzzz", self.registers)
        expected_table = """{{RERegister
|ALPHABET=be
|VG=a
|NF=
|NFNF=
|SUM=1000
|UNK=100
|KOR=300
|FER=500
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
|Abel
|style="background:#FFCBCB"|1998
|-
||III,1
||
|-
|data-sort-value="charlie"|[[RE:Charlie|'''{{Anker2|Charlie}}''']]
||III,1
||
|[[Special:Filepath/Pauly-Wissowa_III,1,_0003.jpg|4]]
|Abel
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
