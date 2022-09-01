from pywikibot import Site

from tools.bots.pi import CanonicalBot
from tools.petscan import PetScan


class Protect(CanonicalBot):
    # pylint: disable=bare-except,too-many-branches,broad-except
    def __init__(self, wiki, debug):
        CanonicalBot.__init__(self, wiki, debug)
        self.searcher = PetScan()

    def task(self) -> bool:
        print("just run for now")
        return True

if __name__ == "__main__":
    WS_WIKI = Site(code="de", fam="wikisource", user="THEprotectIT")
    with Protect(wiki=WS_WIKI, debug=True) as bot:
        bot.run()
