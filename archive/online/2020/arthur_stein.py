from pywikibot import Site, Page

from tools.bots.pi import OneTimeBot
from tools.petscan import PetScan


class ArthurStein(OneTimeBot):
    @staticmethod
    def get_list():
        searcher = PetScan()
        searcher.add_positive_category("RE:Autor:Arthur Stein")
        searcher.add_namespace(0)
        return searcher.run()

    def task(self):
        list_platzhalter = []
        list_protected = []
        lemma_list = self.get_list()
        for idx, item in enumerate(lemma_list):
            lemma = Page(self.wiki, item["title"])
            if self.is_protected(lemma):
                list_protected.append(lemma.title())
            categories = [item.title() for item in lemma.categories()]
            if "Kategorie:RE:Platzhalter" in categories:
                list_platzhalter.append(lemma.title())
            self.logger.info(f"{idx}/{len(lemma_list)} prot: {len(list_protected)}, plat: {len(list_platzhalter)} {lemma.title()}")

        page_protected = Page(self.wiki, "Benutzer:THE IT/RE/Arthur Stein/protected")
        page_protected.text = self.join_lists(list_protected)
        page_protected.save()

        page_platzhalter= Page(self.wiki, "Benutzer:THE IT/RE/Arthur Stein/platzhalter")
        page_platzhalter.text = self.join_lists(list_platzhalter)
        page_platzhalter.save()
        return True

    @staticmethod
    def join_lists(some_list) -> str:
        snippet = "]]\n* [["
        return f"* [[{snippet.join(some_list)}]]"

    @staticmethod
    def is_protected(lemma: Page) -> bool:
        protection_dict = lemma.protection()
        if "edit" in protection_dict.keys():
            if protection_dict["edit"][0] == "sysop":
                return True
        return False


if __name__ == "__main__":
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    with ArthurStein(wiki=WS_WIKI, debug=False, log_to_screen=True, log_to_wiki=False) as bot:
        bot.run()
