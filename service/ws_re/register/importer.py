import re
from datetime import datetime
from typing import Optional

from pywikibot import Site, Page, Category

from service.ws_re.register.registers import Registers
from tools import save_if_changed
from tools.bots.cloud_bot import CloudBot


class ReImporter(CloudBot):
    def __init__(self, wiki: Site = None, debug: bool = True,
                 log_to_screen: bool = True, log_to_wiki: bool = True):
        super().__init__(wiki, debug, log_to_screen, log_to_wiki)
        self.registers = Registers()
        self.new_articles: dict[str, dict[str, str]] = {}
        self._create_neuland()
        self.current_year = datetime.now().year
        self.max_create = min(10, 1000 - len(list(Category(self.wiki, "RE:Stammdaten überprüfen").articles())))

    def _create_neuland(self):
        for number in [1, 2, 3, 4, 5, 6, 7, 11, 12, 13]:
            neuland = Page(self.wiki, f"Wikisource:RE-Werkstatt/Neuland {number}")
            for raw in re.finditer(r"(\{\{REDaten.*?\{\{REAutor\|.*?\}\})\n\d{1,5}\s*„RE:(.*?)“", neuland.text,
                                   re.DOTALL):
                lemma = raw.group(2)
                article = raw.group(1)
                if match := re.search(r"BAND=(.{1,10})\n", article):
                    band = match.group(1)
                    if band not in self.new_articles:
                        self.new_articles[band] = {}
                    self.new_articles[band][lemma] = article

    def task(self):
        # pylint: disable=too-many-nested-blocks
        create_count = 0
        for register in self.registers.volumes.values():
            if create_count >= self.max_create:
                break
            for article in register:
                if article.proof_read is None:
                    if article.get_public_domain_year() < self.current_year:
                        lemma = Page(self.wiki, f"RE:{article.lemma}")
                        if not lemma.exists():
                            article_text = self.get_text(article.volume.name, article.lemma)
                            if article_text:
                                article_text = (f"{article_text}\n[[Kategorie:RE:Stammdaten überprüfen]]"
                                                "\n[[Kategorie:RE:Kurztext überprüfen]]")
                                save_if_changed(lemma, article_text, "Automatisch generiert")
                                create_count += 1
                                if create_count >= self.max_create:
                                    self.logger.info(
                                        f"Created {create_count} articles. Last article was [[RE:{article.lemma}]]"
                                        f" in {register.volume.name}")
                                    break
        return True

    def get_text(self, band: str, article: str) -> Optional[str]:
        band_dict = self.new_articles.get(band, None)
        if band_dict:
            article_text = band_dict.get(article, None)
            if article_text:
                return article_text
        return None


if __name__ == "__main__":  # pragma: no cover
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    with ReImporter(wiki=WS_WIKI, debug=True, log_to_wiki=False) as bot:
        bot.run()
