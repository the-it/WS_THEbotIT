from contextlib import suppress
from datetime import datetime, timedelta

import pywikibot
from pywikibot import Site, Page, exceptions

from tools.bots import BotException
from tools.bots.cloud_bot import CloudBot
from tools.petscan import PetScan, get_processed_time


class Protect(CloudBot):
    def __init__(self, wiki: Site = None, debug: bool = True, log_to_screen: bool = True, log_to_wiki: bool = True):
        CloudBot.__init__(self, wiki, debug, log_to_screen, log_to_wiki)
        self.timeout: timedelta = timedelta(minutes=30)

    def __enter__(self):
        super().__enter__()
        if not self.data:
            self.logger.warning("Try to get the deprecated data back.")
            try:
                self.data.get_deprecated()
            except BotException:
                self.logger.warning("There isn't deprecated data to reload.")
        return self

    @staticmethod
    def _prepare_searcher() -> PetScan:
        searcher = PetScan()
        searcher.add_positive_category("Fertig")
        searcher.add_negative_category("Korrigiert")
        searcher.add_negative_category("Unkorrigiert")
        searcher.add_negative_category("Unvollständig")
        searcher.add_namespace(["Article", "Seite"])
        searcher.set_sort_criteria("date")
        searcher.set_sortorder_decending()
        searcher.set_search_depth(1)
        searcher.set_timeout(120)
        return searcher

    def task(self) -> bool:
        searcher = self._prepare_searcher()
        self.logger.info(str(searcher))
        lemma_list, _ = searcher.get_combined_lemma_list(self.data)
        protected_lemmas = 0
        for idx, lemma_str in enumerate(lemma_list):
            lemma = Page(self.wiki, lemma_str)
            fertig_cat = self._has_fertig_cat(lemma)
            if not fertig_cat:
                with suppress(KeyError):
                    del self.data[lemma_str]
                continue
            self.data[lemma_str] = get_processed_time()
            self.logger.debug(f"check lemma {lemma.title()} for protection")
            if not lemma.protection():
                self.logger.debug(f"protect lemma {lemma.title()}")
                try:
                    lemma.protect(reason="Schutz fertiger Seiten",
                                  protections={'move': 'autoconfirmed', 'edit': 'autoconfirmed'})
                    protected_lemmas += 1
                except exceptions.APIError as error:
                    self.logger.error(f"Wasn't able to protect {lemma.title()}, error was {error}")
            if self._watchdog():
                self.logger.info(f"checked {idx + 1} lemmas")
                self.logger.info(f"{protected_lemmas} lemmas protected")
                self.logger.info(f"oldest_timestamp: {datetime.strptime(min(self.data.values()), '%Y%m%d%H%M%S')}")
                self.logger.info(f"lemmas in storage: {len(self.data)}")
                break
        return True

    @staticmethod
    def _has_fertig_cat(lemma: pywikibot.Page) -> bool:
        categories: list[str] = [category.title() for category in lemma.categories()]
        fertig_cat = False
        for category in categories:
            if not category.find("Fertig") < 0:
                fertig_cat = True
                break
        return fertig_cat


# PYWIKIBOT_DIR=/home/erik/.pywikibot_protect

if __name__ == "__main__":
    WS_WIKI = Site(code="de", fam="wikisource", user="THEprotectIT")
    with Protect(wiki=WS_WIKI, debug=False) as bot:
        bot.run()
