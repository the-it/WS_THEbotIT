# pylint: disable=no-self-use,protected-access
from collections import OrderedDict

from testfixtures import compare

from service.ws_re.register.authors import Authors
from service.ws_re.register.lemma import Lemma
from service.ws_re.register.register_types.alphabetic import AlphabeticRegister
from service.ws_re.register.register_types.volume import VolumeRegister
from service.ws_re.register.test_base import BaseTestRegister, copy_tst_data
from service.ws_re.volumes import Volumes


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
        compare("Aal", a_register[0].lemma)
        compare("Baaba", a_register[4].lemma)
        compare("Beta", b_register[0].lemma)
        compare("Vaaa", b_register[4].lemma)
        compare("Ueee", b_register[5].lemma)

    def test_squash_lemmas(self):
        register = AlphabeticRegister("a", "be", None, "zzzzzz", OrderedDict())
        lemma1 = Lemma.from_dict({"lemma": "lemma", "chapters": [{"start": 1, "end": 1, "author": "Abel"}]},
                       Volumes()["I,1"],
                       self.authors)
        lemma2 = Lemma.from_dict({"lemma": "lemma", "chapters": [{"start": 1, "end": 1, "author": "Abel"}]},
                       Volumes()["III,1"],
                       self.authors)
        lemma3 = Lemma.from_dict({"lemma": "lemma2", "chapters": [{"start": 1, "end": 1, "author": "Abel"}]},
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
|FER=1
|KOR=1
|UNK=3
}}
"""
        compare(expected_header, a_register._get_header())
        expected_header = """{{RERegister
|ALPHABET=be
|VG=a
|NF=c
|NFNF=zzzzzz
|SUM=2
|FER=1
|KOR=0
|UNK=1
}}
"""
        compare(expected_header, b_register._get_header())
        expected_header = """{{RERegister
|ALPHABET=c
|VG=be
|NF=zzzzzz
|SUM=4
|FER=2
|KOR=1
|UNK=1
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
|FER=3
|KOR=1
|UNK=2
}}

{{Tabellenstile}}
{|class="wikitable sortable tabelle-kopf-fixiert" style="background:#FFFAF0;"
!Artikel
!Kurztext
!Wikilinks
!Band
!Seite
!Autor
!Stat
|-
|rowspan=3 data-sort-value="beta"|[[RE:Beta|'''{{Anker2|Beta}}''']]
|rowspan=3|This is Beta 1
|rowspan=3 data-sort-value="w:de:beta"|[[w:de:Beta|Beta<sup>(WP de)</sup>]]<br/>[[s:en:Author:Beta|Beta<sup>(WS en)</sup>]]<br/>[[d:Q123456|WD-Item]]
|rowspan=2|I,1
|[http://elexikon.ch/RE/I,1_5 4]
|Abert
|rowspan=2 style="background:#669966"|FER
|-
|[http://elexikon.ch/RE/I,1_5 4]-5
|Herman Abel
|-
||III,1
||
||
|style="background:#AA0000"|UNK
|-
|data-sort-value="charlie"|[[RE:Charlie|'''{{Anker2|Charlie}}''']]
||
||
||III,1
|[http://elexikon.ch/RE/III,1_5 4]
|Herman Abel
|style="background:#669966"|FER
|-
|data-sort-value="delta"|[[RE:Delta|'''{{Anker2|Delta}}''']]
||
||
||III,1
|[http://elexikon.ch/RE/III,1_5 4]
|Abert
|style="background:#556B2F"|KOR
|-
|data-sort-value="uaaa"|[[RE:Vaaa|'''{{Anker2|Vaaa}}''']]
||
||
||III,1
|[http://elexikon.ch/RE/III,1_5 4]
|Abert
|style="background:#669966"|FER
|-
|data-sort-value="ueee"|[[RE:Ueee|'''{{Anker2|Ueee}}''']]
||
||
||III,1
|[http://elexikon.ch/RE/III,1_5 4]
|Abert
|style="background:#FFFFFF"|
|}
[[Kategorie:RE:Register|!]]"""
        compare(expected_table, b_register.get_register_str())
