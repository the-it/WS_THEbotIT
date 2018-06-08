from pywikibot import Site

from tools.bots import OneTimeBot
from tools.template_handler import TemplateHandler


class ConvertDeprecatedReTemplates(OneTimeBot):
    @staticmethod
    def convet_re_nachtrag(template):
        template_nachtrag = TemplateHandler(template)
        template_daten = TemplateHandler()
        new_list = template_nachtrag.get_parameterlist()
        new_list.append({"key": "NACHTRAG", "value": "ON"})
        template_daten.update_parameters(new_list)
        template_daten.set_title("REDaten")

        return template_daten.get_str()

    @staticmethod
    def _gemeinfrei_todesjahr(argument_list: list):
        for idx, item in enumerate(argument_list):
            if item["key"] == "GEMEINFREI":
                year = item["value"]
                del argument_list[idx]
                if year:
                    try:
                        argument_list.insert(idx,
                                             {"key": "TODESJAHR", "value": str(int(year) - 71)})
                    except ValueError:
                        raise ValueError("year is strange")
                else:
                    argument_list.insert(idx, {"key": "TODESJAHR", "value": "3333"})
        return argument_list

    def convet_re_platzhalter(self, template: str):
        template_platzhalter = TemplateHandler(template)
        template_daten = TemplateHandler()
        new_list = template_platzhalter.get_parameterlist()
        new_list = self._gemeinfrei_todesjahr(new_list)
        template_daten.update_parameters(new_list)
        template_daten.set_title("REDaten")

        return template_daten.get_str()

    def convet_re_nachtrag_platzhalter(self, template: str):
        template_platzhalter = TemplateHandler(template)
        template_daten = TemplateHandler()
        new_list = template_platzhalter.get_parameterlist()
        new_list.append({"key": "NACHTRAG", "value": "ON"})
        new_list = self._gemeinfrei_todesjahr(new_list)
        template_daten.update_parameters(new_list)
        template_daten.set_title("REDaten")

        return template_daten.get_str()

    def task(self):
        print(self)
        return True


if __name__ == "__main__":
    WIKI = Site(code='de', fam='wikisource', user='THEbotIT')
    with ConvertDeprecatedReTemplates(wiki=WIKI, debug=True) as bot:
        bot.run()
