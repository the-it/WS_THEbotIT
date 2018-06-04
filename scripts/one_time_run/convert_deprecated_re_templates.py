from pywikibot import Site

from test import *
from tools.bots import OneTimeBot
from tools.template_handler import TemplateFinder, TemplateHandler



class ConvertDeprecatedReTemplates(OneTimeBot):
    @staticmethod
    def convet_re_nachtrag(template):
        template_nachtrag = TemplateHandler(template)
        template_daten = TemplateHandler()
        new_dict = template_nachtrag.get_parameterlist()
        new_dict.append({"key": "NACHTRAG", "value": "ON"})
        template_daten.update_parameters(new_dict)
        template_daten.set_title("REDaten")

        return template_daten.get_str()

    def task(self):
        return True


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

if __name__ == "__main__":
    WIKI = Site(code='de', fam='wikisource', user='THEbotIT')
    with ConvertDeprecatedReTemplates(wiki=WIKI, debug=True) as bot:
        bot.run()
