from datetime import datetime

from pywikibot import Site

from tools.bots import BotException
from tools.bots.pi import CanonicalBot
from tools.petscan import PetScan


class Protect(CanonicalBot):
    def __init__(self, wiki, debug):
        CanonicalBot.__init__(self, wiki, debug, log_to_wiki=False)

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
        print(len(lemma_list))
        for idx, lemma in enumerate(lemma_list):
            self.data[lemma] = datetime.now().strftime("%Y%m%d%H%M%S")
        return True


if __name__ == "__main__":
    WS_WIKI = Site(code="de", fam="wikisource", user="THEprotectIT")
    with Protect(wiki=WS_WIKI, debug=True) as bot:
        bot.run()
