from datetime import datetime
from operator import itemgetter

from pywikibot import Site

from tools._typing import PetscanLemma
from tools.bots import BotException
from tools.bots.pi import CanonicalBot
from tools.petscan import PetScan


class Protect(CanonicalBot):
    # pylint: disable=bare-except,too-many-branches,broad-except
    def __init__(self, wiki, debug):
        CanonicalBot.__init__(self, wiki, debug, log_to_wiki=False)
        self.searcher = PetScan()

    def __enter__(self):
        super().__enter__()
        if not self.data:
            self.logger.warning("Try to get the deprecated data back.")
            try:
                self.data.get_deprecated()
            except BotException:
                self.logger.warning("There isn't deprecated data to reload.")
        return self

    def compile_lemma_list(self) -> list[str]:
        self.logger.info("Compile the lemma list")
        raw_lemma_list = self._petscan_search()
        # all items which wasn't process before
        new_lemma_list = []
        for lemma in raw_lemma_list:
            try:
                self.data[lemma]
            except KeyError:
                new_lemma_list.append(lemma)
        # before processed lemmas ordered by last process time
        old_lemma_list = [x[0] for x in sorted(self.data.items(), key=itemgetter(1))]
        # first iterate new items then the old ones (oldest first)
        return new_lemma_list + old_lemma_list

    def _petscan_search(self) -> list[str]:
        searcher = PetScan()
        searcher.add_positive_category("Fertig")
        searcher.set_sort_criteria("date")
        searcher.set_sortorder_decending()
        searcher.set_timeout(120)

        self.logger.info(f"[{searcher} {searcher}]")
        raw_lemma_list = searcher.run()
        return [item["nstext"] + ":" + item["title"] for item in raw_lemma_list]

    def task(self) -> bool:
        print("just run for now")
        lemma_list = self.compile_lemma_list()
        for idx, lemma in enumerate(lemma_list):
            print(idx, lemma)
            self.data[lemma] = datetime.now().strftime("%Y%m%d%H%M%S")
        return True

if __name__ == "__main__":
    WS_WIKI = Site(code="de", fam="wikisource", user="THEprotectIT")
    with Protect(wiki=WS_WIKI, debug=True) as bot:
        bot.run()
