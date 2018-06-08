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
        compare(post_text, ConvertDeprecatedReTemplates().convet_re_nachtrag(pre_text))

    def test_convert_platzhalter(self):
        pre_text = """{{RENachtrag/Platzhalter
|BAND=S I
|SPALTE_START=267
|SPALTE_END=OFF
|VORGÄNGER=Caecilius 42
|NACHFOLGER=Caecilius 54a
|SORTIERUNG=
|KORREKTURSTAND=korrigiert
|KEINE_SCHÖPFUNGSHÖHE=
|GEMEINFREI=2071
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
|TODESJAHR=2000
|WIKIPEDIA=
|WIKISOURCE=
|EXTSCAN_START={{REIA|S I|267}}
|EXTSCAN_END=
|ÜBERSCHRIFT=ON
}}"""
        compare(post_text, ConvertDeprecatedReTemplates().convet_re_platzhalter(pre_text))

    def test_convert_platzhalter_no_year(self):
        pre_text = """{{RENachtrag/Platzhalter
|GEMEINFREI=
|ÜBERSCHRIFT=ON
}}"""
        post_text = """{{REDaten
|TODESJAHR=3333
|ÜBERSCHRIFT=ON
}}"""
        compare(post_text, ConvertDeprecatedReTemplates().convet_re_platzhalter(pre_text))

    def test_convert_platzhalter_strange_year(self):
        pre_text = """{{RENachtrag/Platzhalter
|GEMEINFREI=abcd
|ÜBERSCHRIFT=ON
}}"""
        with self.assertRaises(ValueError):
            ConvertDeprecatedReTemplates().convet_re_platzhalter(pre_text)

    def test_convert_platzhalter_death_year(self):
        pre_text = """{{RENachtrag/Platzhalter
|TODESJAHR=1988
|ÜBERSCHRIFT=ON
}}"""
        post_text = """{{REDaten
|TODESJAHR=1988
|ÜBERSCHRIFT=ON
}}"""
        compare(post_text, ConvertDeprecatedReTemplates().convet_re_platzhalter(pre_text))

    def test_convert_nachtrag_platzhalter(self):
        pre_text = """{{RENachtrag/Platzhalter
|BAND=S I
|SPALTE_START=267
|SPALTE_END=OFF
|VORGÄNGER=Caecilius 42
|NACHFOLGER=Caecilius 54a
|SORTIERUNG=
|KORREKTURSTAND=korrigiert
|KEINE_SCHÖPFUNGSHÖHE=
|GEMEINFREI=2071
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
|TODESJAHR=2000
|WIKIPEDIA=
|WIKISOURCE=
|EXTSCAN_START={{REIA|S I|267}}
|EXTSCAN_END=
|ÜBERSCHRIFT=ON
|NACHTRAG=ON
}}"""
        compare(post_text, ConvertDeprecatedReTemplates().convet_re_nachtrag_platzhalter(pre_text))