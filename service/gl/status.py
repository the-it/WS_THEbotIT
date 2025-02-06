import re

from pywikibot import Page, Site

from tools.bots.pi import CanonicalBot
from tools.petscan import PetScan


class GlStatus(CanonicalBot):
    def __init__(self, wiki, debug):
        CanonicalBot.__init__(self, wiki, debug)

    def task(self):
        if self.debug:  # activate for debug purpose
            lemma = "Benutzer:THEbotIT/" + self.bot_name
        else:
            lemma = "Die Gartenlaube"
        page = Page(self.wiki, lemma)
        temp_text = page.text

        alle = self.petscan([])
        fertig = self.petscan(["Fertig"])
        korrigiert = self.petscan(["Korrigiert"])
        unkorrigiert = self.petscan(["Unkorrigiert"])
        articles = self.petscan([], article=True, not_categories=["Die Gartenlaube Hefte"])

        temp_text = self.projektstand(temp_text, alle, fertig, korrigiert, unkorrigiert, articles)
        temp_text = self.alle_seiten(temp_text, alle)
        temp_text = self.korrigierte_seiten(temp_text, korrigiert)
        temp_text = self.fertige_seiten(temp_text, fertig)
        for year in range(1853, 1900):
            temp_text = self.year(year, temp_text)

        page.text = temp_text
        page.save("Ein neuer Datensatz wurde eingefügt.", bot=True)
        return True

    @staticmethod
    def to_percent(counter, denominator):
        return f" ({round((counter / denominator) * 100, 2):.2f} %)".replace(".", ",")

    def projektstand(self, temp_text, alle, fertig, korrigiert, unkorrigiert, articles):
        # pylint: disable=too-many-arguments
        composed_text = "".join(["<!--new line: "
                                 "Liste wird von einem Bot aktuell gehalten.-->\n|-\n",
                                 "|",
                                 self.timestamp.start_of_run.strftime("%d.%m.%Y"),
                                 "|| ", str(alle),
                                 " || ", str(unkorrigiert), self.to_percent(unkorrigiert, alle),
                                 " || ", str(korrigiert), self.to_percent(korrigiert, alle),
                                 " || ", str(fertig), self.to_percent(fertig, alle),
                                 " || ", str(articles) + "/18500", self.to_percent(articles, 18500),
                                 " ||"])
        return re.sub("<!--new line: Liste wird von einem Bot aktuell gehalten.-->",
                      composed_text, temp_text)

    @staticmethod
    def alle_seiten(temp_text, all_lemmas):
        composed_text = "".join(["<!--GLStatus:alle_Seiten-->", str(all_lemmas), "<!---->"])
        temp_text = re.sub(r"<!--GLStatus:alle_Seiten-->\d{5}<!---->", composed_text, temp_text)
        return temp_text

    @staticmethod
    def korrigierte_seiten(temp_text, korrigiert):
        composed_text = "".join(["<!--GLStatus:korrigierte_Seiten-->", str(korrigiert), "<!---->"])
        temp_text = \
            re.sub(r"<!--GLStatus:korrigierte_Seiten-->\d{5}<!---->", composed_text, temp_text)
        return temp_text

    @staticmethod
    def fertige_seiten(temp_text, fertig):
        composed_text = "".join(["<!--GLStatus:fertige_Seiten-->", str(fertig), "<!---->"])
        temp_text = \
            re.sub(r"<!--GLStatus:fertige_Seiten-->\d{4,5}<!---->", composed_text, temp_text)
        return temp_text

    def year(self, year, temp_text):
        fertig = self.petscan(["Fertig"], year=year)
        korrigiert = self.petscan(["Korrigiert"], year=year)
        rest = self.petscan([], not_categories=["Fertig", "Korrigiert"], year=year)
        alle = fertig + korrigiert + rest
        regex = re.compile("<!--GLStatus:" + str(year) + "-->.*?<!---->")
        if rest > 0:
            temp_text = regex.sub(
                f"<!--GLStatus:{year}-->"
                "|span style=\"background-color:#4876FF; "
                f"font-weight: bold\"|ca. {str(round(((fertig + korrigiert) / alle) * 100, 1)).replace('.', ',')} "
                "% korrigiert oder fertig"
                "<!---->",
                temp_text)
        elif korrigiert > 0:
            temp_text = regex.sub(
                f"<!--GLStatus:{year}-->"
                "|span style=\"background-color:#F7D700; "
                f"font-weight: bold\"|{str(round((fertig / alle) * 100, 1)).replace('.', ',')} "
                "% fertig, Rest korrigiert"
                "<!---->",
                temp_text)
        else:
            temp_text = regex.sub(
                f"<!--GLStatus:{year}-->|span style=\"background-color:#00FF00; "
                f"font-weight: bold\"|Fertig<!---->",
                temp_text)
        return temp_text

    def petscan(self, categories, not_categories=None, article=False, year=None):
        searcher = PetScan()
        searcher.set_timeout(120)
        if article:
            # Article
            searcher.add_namespace(0)
        else:
            # Seite
            searcher.add_namespace(102)
        searcher.set_search_depth(5)
        if year:
            searcher.add_positive_category("Die Gartenlaube (" + str(year) + ")")
        else:
            searcher.add_positive_category("Die Gartenlaube")
        for category in categories:
            searcher.add_positive_category(category)
        if not_categories:
            for category in not_categories:
                searcher.add_negative_category(category)
        self.logger.debug(str(searcher))
        return len(searcher.run())


if __name__ == "__main__":
    WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    with GlStatus(wiki=WIKI, debug=False) as bot:
        bot.run()
