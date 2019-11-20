# pylint: disable=protected-access
from collections import OrderedDict

from testfixtures import compare

from scripts.service.ws_re.register.alphabetic import AlphabeticRegister
from scripts.service.ws_re.register.author import Authors
from scripts.service.ws_re.register.author_register import AuthorRegister
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
        abel_register = AuthorRegister(self.authors.get_author("Abel"), self.authors, self.registers)
        compare(4, len(abel_register))

    def test_make_table(self):
        abel_register = AuthorRegister(self.authors.get_author("Abel"), self.authors, self.registers)
        expected_table = """{{RERegister
|AUTHOR=Abel
|SUM=4
|UNK=0
|KOR=1
|FER=2
}}

{|class="wikitable sortable"
!Artikel
!Band
!Wikilinks
!Seite
!Autor
!Sterbejahr
|-
|data-sort-value="aba 001"|[[RE:Aba 1|'''{{Anker2|Aba 1}}''']]
||I,1
||
|[[Special:Filepath/Pauly-Wissowa_I,1,_0003.jpg|4]]
|Abel
|style="background:#FFCBCB"|1998
|-
|data-sort-value="aba 002"|[[RE:Aba 2|'''{{Anker2|Aba 2}}''']]
||I,1
||
|[[Special:Filepath/Pauly-Wissowa_I,1,_0003.jpg|4]]
|Abel
|style="background:#FFCBCB"|1998
|-
|rowspan=2 data-sort-value="beta"|[[RE:Beta|'''{{Anker2|Beta}}''']]
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
|data-sort-value="charlie"|[[RE:Charlie|'''{{Anker2|Charlie}}''']]
||III,1
||
|[[Special:Filepath/Pauly-Wissowa_III,1,_0003.jpg|4]]
|Abel
|style="background:#FFCBCB"|1998
|}
[[Kategorie:RE:Register|!]]
Zahl der Artikel: 4, """
        compare(expected_table, abel_register.get_register_str())
