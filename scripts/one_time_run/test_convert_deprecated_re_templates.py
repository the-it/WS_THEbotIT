from test import *
from .convert_deprecated_re_templates import ConvertDeprecatedReTemplates


class TestConvertDeprecatedReTemplates(TestCase):
    def test_convert_nachtrag(self):
        pre_text = """{{RENachtrag
|BAND=S I
|SPALTE_START=267
|SPALTE_END=OFF
|VORGÄNGER=Caecilius 42
|NACHFOLGER=Caecilius 54a
|SORTIERUNG=
|KORREKTURSTAND=korrigiert
|KEINE_SCHÖPFUNGSHÖHE=
|TODESJAHR=
|WIKIPEDIA=
|WIKISOURCE=
|EXTSCAN_START={{REIA|S I|267}}
|EXTSCAN_END=
|ÜBERSCHRIFT=ON
}}"""
        post_text = """{{REDaten
|BAND=S I
|SPALTE_START=267
|SPALTE_END=OFF
|VORGÄNGER=Caecilius 42
|NACHFOLGER=Caecilius 54a
|SORTIERUNG=
|KORREKTURSTAND=korrigiert
|KEINE_SCHÖPFUNGSHÖHE=
|TODESJAHR=
|WIKIPEDIA=
|WIKISOURCE=
|EXTSCAN_START={{REIA|S I|267}}
|EXTSCAN_END=
|ÜBERSCHRIFT=ON
|NACHTRAG=ON
}}"""
        compare(post_text, ConvertDeprecatedReTemplates.convet_re_nachtrag(pre_text))

