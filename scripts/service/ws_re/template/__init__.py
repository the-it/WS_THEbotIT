class ReDatenException(Exception):
    pass


RE_DATEN = "REDaten"
RE_ABSCHNITT = "REAbschnitt"
RE_AUTHOR = "REAutor"
ARTICLE_TEMPLATE = """{{REDaten
|BAND=
|SPALTE_START=
|SPALTE_END=
|VORGÄNGER=
|NACHFOLGER=
|SORTIERUNG=
|KORREKTURSTAND=
|WIKIPEDIA=
|WIKISOURCE=
|EXTSCAN_START=
|EXTSCAN_END=
|GND=
|KEINE_SCHÖPFUNGSHÖHE=OFF
|TODESJAHR=
|GEBURTSJAHR=
|NACHTRAG=OFF
|ÜBERSCHRIFT=OFF
|VERWEIS=OFF
}}
text
{{REAutor|Autor.}}"""
