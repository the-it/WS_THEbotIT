from datetime import datetime, timedelta

from pywikibot import Site, Page

from tools.bots import BotException
from tools.bots.pi import CanonicalBot
from tools.petscan import PetScan


class Protect(CanonicalBot):
    def __init__(self, wiki, debug):
        CanonicalBot.__init__(self, wiki, debug)
        self.timeout: timedelta = timedelta(hours=4)

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
        searcher.set_sort_criteria("date")
        searcher.set_sortorder_decending()
        searcher.set_search_depth(1)
        searcher.set_timeout(120)
        return searcher

    def task(self) -> bool:
        searcher = self._prepare_searcher()
        self.logger.info(str(searcher))
        lemma_list = searcher.get_combined_lemma_list(self.data)
        protected_lemmas = 0
        for idx, lemma_str in enumerate(lemma_list):
            self.data[lemma_str] = datetime.now().strftime("%Y%m%d%H%M%S")
            lemma = Page(self.wiki, lemma_str)
            self.logger.debug(f"check lemma {lemma.title()} for protection")
            if not lemma.protection():
                self.logger.debug(f"protect lemma {lemma.title()}")
                protected_lemmas += 1
                lemma.protect(reason="Schutz fertiger Seiten",
                              protections={'move': 'autoconfirmed', 'edit': 'autoconfirmed'})
            if self._watchdog():
                self.logger.info(f"checked {idx + 1} lemmas")
                self.logger.info(f"{protected_lemmas} lemmas protected")
                self.logger.info(f"oldest_timestamp: {datetime.strptime(min(self.data.values()), '%Y%m%d%H%M%S')}")
                self.logger.info(f"lemmas in storgae: {len(self.data)}")
                break
        return True


# PYWIKIBOT_DIR=/home/esommer/.pywikibot_protect

if __name__ == "__main__":
    WS_WIKI = Site(code="de", fam="wikisource", user="THEprotectIT")
    with Protect(wiki=WS_WIKI, debug=False) as bot:
        bot.run()
