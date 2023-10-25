import re

from pywikibot import Site, Page

from tools.bots.pi import OneTimeBot
from tools.petscan import PetScan


class AachenerStadtrechnung(OneTimeBot):
    @staticmethod
    def get_list():
        searcher = PetScan()
        searcher.add_positive_category("Aachener Stadtrechnungen")
        searcher.add_namespace(0)
        return searcher.run()

    cat_list = ["Neuhochdeutsch", "Mittelniederdeutsch", "Latein", "Josef Laurent",
                "Geschichte", "Deutschland", "Darstellung", "14. Jahrhundert", "Werke"]

    def task(self):
        for idx, item in enumerate(self.get_list()):
            lemma = Page(self.wiki, item["title"])
            temp_text = lemma.text
            for cat in self.cat_list:
                temp_text = re.sub(f"\[\[Kategorie:{cat}\]\]\n?", "", temp_text)
            lemma.text = temp_text
            lemma.save("remove categories")
        return True


if __name__ == "__main__":
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    with AachenerStadtrechnung(wiki=WS_WIKI, debug=False, log_to_screen=False, log_to_wiki=False) as bot:
        bot.run()
