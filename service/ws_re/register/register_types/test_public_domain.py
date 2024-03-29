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
        expected_table = """{{Tabellenstile}}
{|class="wikitable sortable tabelle-kopf-fixiert"
!Artikel
!Kurztext
!Wikilinks
!Band
!Seite
!Autor
!Stat
|-
|data-sort-value="aal"|[[RE:Aal|'''{{Anker2|Aal}}''']]
||
||
||I,1
|[http://elexikon.ch/RE/I,1_1.png 1]-4
|William Abbott
|style="background:#AA0000"|UNK
|-
|data-sort-value="aba 001"|[[RE:Aba 1|'''{{Anker2|Aba 1}}''']]
||This is Aba 1
||
||I,1
|[http://elexikon.ch/RE/I,1_5.png 4]
|Herman Abel
|style="background:#AA0000"|UNK
|-
|data-sort-value="aba 002"|[[RE:Aba 2|'''{{Anker2|Aba 2}}''']]
||
||
||I,1
|[http://elexikon.ch/RE/I,1_5.png 4]
|Herman Abel
|style="background:#556B2F"|KOR
|-
|data-sort-value="adam"|[[RE:Adam|'''{{Anker2|Adam}}''']]
||
||
||III,1
|[http://elexikon.ch/RE/III,1_1.png 1]-4
|William Abbott
|style="background:#AA0000"|UNK
|-
|rowspan=2 data-sort-value="beta"|[[RE:Beta|'''{{Anker2|Beta}}''']]
|rowspan=2|This is Beta
|rowspan=2|
|rowspan=2|I,1
|[http://elexikon.ch/RE/I,1_5.png 4]
|Abert
|rowspan=2 style="background:#669966"|FER
|-
|[http://elexikon.ch/RE/I,1_5.png 4]-5
|Herman Abel
|-
|data-sort-value="charlie"|[[RE:Charlie|'''{{Anker2|Charlie}}''']]
||
||
||III,1
|[http://elexikon.ch/RE/III,1_5.png 4]
|Herman Abel
|style="background:#669966"|FER
|}
[[Kategorie:RE:Register|!]]"""
        compare(expected_table, pd_2021_register.get_register_str())
