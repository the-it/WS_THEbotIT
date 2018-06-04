from pywikibot import Site

from tools.bots import OneTimeBot
from tools.template_handler import TemplateHandler


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
        print(self)
        return True


if __name__ == "__main__":
    WIKI = Site(code='de', fam='wikisource', user='THEbotIT')
    with ConvertDeprecatedReTemplates(wiki=WIKI, debug=True) as bot:
        bot.run()
