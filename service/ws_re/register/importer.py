import re
from typing import Optional

import pywikibot
from pywikibot import Site, Page

from service.ws_re.register.registers import Registers
from tools import save_if_changed
from tools.bots.cloud_bot import CloudBot


class ReImporter(CloudBot):
    def __init__(self, wiki: Site = None, debug: bool = True,
                 log_to_screen: bool = True, log_to_wiki: bool = True):
        super().__init__(wiki, debug, log_to_screen, log_to_wiki)
        self.registers = Registers()
        self.new_articles: dict[str, dict[str, str]] = {}
        #self._create_neuland()

    def _create_neuland(self):
        for number in [1, 2, 3, 4, 5, 6, 7, 11, 12, 13]:
            neuland = Page(self.wiki, f"Wikisource:RE-Werkstatt/Neuland {number}")
            for raw in re.finditer(r"(\{\{REDaten.*?\{\{REAutor\|.*?\}\})\n\d{1,5}\s*„RE:(.*?)“", neuland.text,
                                   re.DOTALL):
                lemma = raw.group(2)
                article = raw.group(1)
                band = re.search(r"BAND=(.{1,10})\n", article).group(1)
                if band not in self.new_articles.keys():
                    self.new_articles[band] = {}
                self.new_articles[band][lemma] = article

    def task(self):
        for register in self.registers.volumes.values():
            for article in register:
                if article.proof_read is None:
                    lemma = Page(self.wiki, f"RE:{article.lemma}")
                    if not lemma.exists():
                        article_text = self.get_text(article.volume.name, article.lemma)
                        if article_text:
                            article_text = (article_text +
                                            "\n[[Kategorie:RE:Stammdaten überprüfen]]"
                                            "\n[[Kategorie:RE:Kurztext überprüfen]]")
                            save_if_changed(lemma, article_text, "Automatisch generiert")

    def get_text(self, band: str, article: str) -> Optional[str]:
        band = self.new_articles.get(band, None)
        if band:
            article_text = band.get(article, None)
            if article_text:
                return article_text
        return None


if __name__ == "__main__":  # pragma: no cover
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    with ReImporter(wiki=WS_WIKI, debug=True, log_to_wiki=False) as bot:
        bot.run()
