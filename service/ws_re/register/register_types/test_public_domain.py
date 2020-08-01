# pylint: disable=protected-access
from collections import OrderedDict

from testfixtures import compare

from service.ws_re.register.authors import Authors
from service.ws_re.register.register_types.public_domain import PublicDomainRegister
from service.ws_re.register.register_types.volume import VolumeRegister
from service.ws_re.register.test_base import BaseTestRegister, copy_tst_data
from service.ws_re.volumes import Volumes


class TestPublicDomainRegister(BaseTestRegister):
    def setUp(self):
        copy_tst_data("authors_pd_register", "authors")
        copy_tst_data("I_1_alpha", "I_1")
        copy_tst_data("III_1_alpha", "III_1")
        self.authors = Authors()
        self.volumes = Volumes()
        self.registers = OrderedDict()
        self.registers["I,1"] = VolumeRegister(self.volumes["I,1"], self.authors)
        self.registers["III,1"] = VolumeRegister(self.volumes["III,1"], self.authors)

    def test_pd_authors(self):
        pd_2021_register = PublicDomainRegister(2021, self.authors, self.registers)
        compare(2, len(pd_2021_register._get_pd_authors()))

    def test_init(self):
        pd_2021_register = PublicDomainRegister(2021, self.authors, self.registers)
        compare(6, len(pd_2021_register))

    def test_make_table(self):
        pd_2021_register = PublicDomainRegister(2021, self.authors, self.registers)
        expected_table = """{|class="wikitable sortable"
!Artikel
!Band
!Status
!Wikilinks
!Seite
!Autor
!Sterbejahr
|-
|data-sort-value="aal"|[[RE:Aal|'''{{Anker2|Aal}}''']]
||I,1
|style="background:#AA0000"|UNK
||
|[[Special:Filepath/Pauly-Wissowa_I,1,_0001.jpg|1]]-4
|William Abbott
|style="background:#CBCBCB"|
|-
|data-sort-value="aba 001"|[[RE:Aba 1|'''{{Anker2|Aba 1}}''']]
||I,1
|style="background:#AA0000"|UNK
||
|[[Special:Filepath/Pauly-Wissowa_I,1,_0003.jpg|4]]
|Herman Abel
|style="background:#FFCBCB"|1950
|-
|data-sort-value="aba 002"|[[RE:Aba 2|'''{{Anker2|Aba 2}}''']]
||I,1
|style="background:#556B2F"|KOR
||
|[[Special:Filepath/Pauly-Wissowa_I,1,_0003.jpg|4]]
|Herman Abel
|style="background:#FFCBCB"|1950
|-
|data-sort-value="adam"|[[RE:Adam|'''{{Anker2|Adam}}''']]
||III,1
|style="background:#AA0000"|UNK
||
|[[Special:Filepath/Pauly-Wissowa_III,1,_0001.jpg|1]]-4
|William Abbott
|style="background:#CBCBCB"|
|-
|rowspan=2 data-sort-value="beta"|[[RE:Beta|'''{{Anker2|Beta}}''']]
|rowspan=2 |I,1
|rowspan=2 style="background:#669966"|FER
|rowspan=2 |
|[[Special:Filepath/Pauly-Wissowa_I,1,_0003.jpg|4]]
|Abert
|style="background:#B9FFC5"|1927
|-
|[[Special:Filepath/Pauly-Wissowa_I,1,_0003.jpg|4]]-5
|Herman Abel
|style="background:#FFCBCB"|1950
|-
|data-sort-value="charlie"|[[RE:Charlie|'''{{Anker2|Charlie}}''']]
||III,1
|style="background:#669966"|FER
||
|[[Special:Filepath/Pauly-Wissowa_III,1,_0003.jpg|4]]
|Herman Abel
|style="background:#FFCBCB"|1950
|}
Zahl der Artikel: 6, """
        print(pd_2021_register.get_register_str())
        compare(expected_table, pd_2021_register.get_register_str())
