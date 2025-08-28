# pylint: disable=no-self-use,protected-access
from collections import OrderedDict

from testfixtures import compare

from service.ws_re.register.authors import Authors
from service.ws_re.register.register_types.author import AuthorRegister
from service.ws_re.register.register_types.volume import VolumeRegister
from service.ws_re.register.test_base import BaseTestRegister, copy_tst_data
from service.ws_re.volumes import Volumes


class TestAuthorRegister(BaseTestRegister):
    def setUp(self):
        copy_tst_data("I_1_alpha", "I_1")
        copy_tst_data("III_1_alpha", "III_1")
        self.authors = Authors()
        self.volumes = Volumes()
        self.registers = OrderedDict()
        self.registers["I,1"] = VolumeRegister(self.volumes["I,1"], self.authors)
        self.registers["III,1"] = VolumeRegister(self.volumes["III,1"], self.authors)

    def test_init(self):
        abel_register = AuthorRegister(self.authors.get_author("Herman Abel"), self.authors, self.registers)
        compare(4, len(abel_register))

    def test_make_table(self):
        abel_register = AuthorRegister(self.authors.get_author("Herman Abel"), self.authors, self.registers)
        expected_table = """{{RERegister
|AUTHOR=Herman Abel
|SUM=4
|FER=2
|KOR=1
|NGE=0
|VOR=0
|UNK=1
}}

{{Tabellenstile}}
{|class="wikitable sortable tabelle-kopf-fixiert"
!Artikel
!Kurztext
!Wikilinks
!Band
!Seite
!Autor
!Stat
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
|rowspan=2 data-sort-value="beta"|[[RE:Beta|'''{{Anker2|Beta}}''']]
|rowspan=2|
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
[[Kategorie:RE:Register|Abel, Herman]]"""
        compare(expected_table, abel_register.get_register_str())
        expected_table_less_details = """{{RERegister
|AUTHOR=Herman Abel
|SUM=4
|FER=2
|KOR=1
|NGE=0
|VOR=0
|UNK=1
}}

{{Tabellenstile}}
{|class="wikitable sortable tabelle-kopf-fixiert"
!Artikel

!Wikilinks
!Band
!Seite

!Stat
|-
|data-sort-value="aba 001"|[[RE:Aba 1|'''{{Anker2|Aba 1}}''']]
||
||I,1
|[http://elexikon.ch/RE/I,1_5.png 4]
|style="background:#AA0000"|UNK
|-
|data-sort-value="aba 002"|[[RE:Aba 2|'''{{Anker2|Aba 2}}''']]
||
||I,1
|[http://elexikon.ch/RE/I,1_5.png 4]
|style="background:#556B2F"|KOR
|-
|rowspan=2 data-sort-value="beta"|[[RE:Beta|'''{{Anker2|Beta}}''']]
|rowspan=2|
|rowspan=2|I,1
|[http://elexikon.ch/RE/I,1_5.png 4]
|rowspan=2 style="background:#669966"|FER
|-
|[http://elexikon.ch/RE/I,1_5.png 4]-5
|-
|data-sort-value="charlie"|[[RE:Charlie|'''{{Anker2|Charlie}}''']]
||
||III,1
|[http://elexikon.ch/RE/III,1_5.png 4]
|style="background:#669966"|FER
|}
[[Kategorie:RE:Register|Abel, Herman]]"""
        compare(expected_table_less_details, abel_register.get_register_str(print_details=False))

    def test_overview_line(self):
        abel_register = AuthorRegister(self.authors.get_author("Herman Abel"), self.authors, self.registers)
        compare("|-\n"
                "|data-sort-value=\"Abel, Herman\""
                "|[[Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/Herman Abel|Herman Abel]]\n"
                "|data-sort-value=\"0004\"|4\n"
                "|data-sort-value=\"075.0\"|75.0%\n"
                "|<span style=\"color:#669966\">██████████</span>"
                "<span style=\"color:#556B2F\">█████</span>"
                "<span style=\"color:#FFCBCB\"></span>"
                "<span style=\"color:#9FC859\"></span>"
                "<span style=\"color:#AA0000\">█████</span>",
                abel_register.overview_line)

    def test_proofread_parts_of_20(self):
        compare((10, 5, 0, 0, 5), AuthorRegister.proofread_parts_of_20(4, 2, 1, 0, 0))
        compare((10, 0, 5, 0, 5), AuthorRegister.proofread_parts_of_20(4, 2, 0, 1, 0))
        compare((10, 0, 0, 5, 5), AuthorRegister.proofread_parts_of_20(4, 2, 0, 0, 1))
        compare((4, 4, 4, 4, 4), AuthorRegister.proofread_parts_of_20(5, 1, 1, 1, 1))
        compare((0, 1, 0, 0, 19), AuthorRegister.proofread_parts_of_20(40, 1, 1, 0, 0))
        compare((1, 0, 0, 0, 19), AuthorRegister.proofread_parts_of_20(45, 2, 1, 0, 0))
        compare((0, 1, 0, 0, 19), AuthorRegister.proofread_parts_of_20(45, 1, 2, 0, 0))
        compare((0, 1, 0, 0, 19), AuthorRegister.proofread_parts_of_20(79, 1, 1, 0, 0))
        compare((0, 0, 0, 0, 20), AuthorRegister.proofread_parts_of_20(80, 1, 1, 0, 0))

    def test_bug_to_much_percent(self):
        copy_tst_data("I_1_author_bug_percent", "I_1")
        copy_tst_data("III_1_author_bug_percent", "III_1")
        registers = OrderedDict()
        registers["I,1"] = VolumeRegister(self.volumes["I,1"], self.authors)
        registers["III,1"] = VolumeRegister(self.volumes["III,1"], self.authors)
        abel_register = AuthorRegister(self.authors.get_author("Herman Abel"), self.authors, registers)
        compare("|-\n"
                "|data-sort-value=\"Abel, Herman\""
                "|[[Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/Herman Abel|Herman Abel]]\n"
                "|data-sort-value=\"0005\"|5\n"
                "|data-sort-value=\"100.0\"|100.0%\n"
                "|<span style=\"color:#669966\">████████████████████</span>"
                "<span style=\"color:#556B2F\"></span>"
                "<span style=\"color:#FFCBCB\"></span>"
                "<span style=\"color:#9FC859\"></span>"
                "<span style=\"color:#AA0000\"></span>",
                abel_register.overview_line)
