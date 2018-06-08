from pywikibot import Site

from tools.bots import OneTimeBot
from tools.template_handler import TemplateHandler, TemplateFinder


class ConvertDeprecatedReTemplates(OneTimeBot):
    @staticmethod
    def convert_re_nachtrag(template: str):
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

    def convert_re_platzhalter(self, template: str):
        template_platzhalter = TemplateHandler(template)
        template_daten = TemplateHandler()
        new_list = template_platzhalter.get_parameterlist()
        new_list = self._gemeinfrei_todesjahr(new_list)
        template_daten.update_parameters(new_list)
        template_daten.set_title("REDaten")

        return template_daten.get_str()

    def convert_re_nachtrag_platzhalter(self, template: str):
        template_platzhalter = TemplateHandler(template)
        template_daten = TemplateHandler()
        new_list = template_platzhalter.get_parameterlist()
        new_list.append({"key": "NACHTRAG", "value": "ON"})
        new_list = self._gemeinfrei_todesjahr(new_list)
        template_daten.update_parameters(new_list)
        template_daten.set_title("REDaten")

        return template_daten.get_str()

    def convert_all(self, article_text: str):
        for template in ("RENachtrag/Platzhalter", "RENachtrag", "REDaten/Platzhalter"):
            position = TemplateFinder(article_text).get_positions(template)
            while position:
                length_article = len(article_text)
                if template == "RENachtrag/Platzhalter":
                    convert_func = self.convert_re_nachtrag_platzhalter
                elif template == "RENachtrag":
                    convert_func = self.convert_re_nachtrag
                else:
                    convert_func = self.convert_re_platzhalter
                start = position[0]["pos"][0]
                end = position[0]["pos"][1]
                pre_article_text = article_text
                article_text = convert_func(position[0]["text"])
                if start > 0:
                    article_text = pre_article_text[0:start] + article_text
                if end < length_article:
                    article_text = article_text + pre_article_text[end:]
                position = TemplateFinder(article_text).get_positions(template)
        return article_text

    def task(self):
        print(self)
        return True


if __name__ == "__main__":
    WIKI = Site(code='de', fam='wikisource', user='THEbotIT')
    with ConvertDeprecatedReTemplates(wiki=WIKI, debug=True) as bot:
        bot.run()
