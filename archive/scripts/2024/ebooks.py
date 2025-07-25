import re

from pywikibot import Site, Page

from archive.service.pi import OneTimeBot
from tools.petscan import PetScan


class Ebooks(OneTimeBot):
    @staticmethod
    def get_list():
        searcher = PetScan()
        searcher.add_yes_template("Ebooks")
        searcher.add_namespace(0)
        return searcher.run()

    def task(self):
        lemma_list = self.get_list()
        for lemma in lemma_list:
            page = Page(self.wiki, lemma['title'])
            text = re.sub(r"( |<br ?\/>|\n|){{Ebooks\|[^}]+}}", "", page.text)
            page.text = text
            page.save("Vorlage Ebooks entfernt.")
            print(page.title())
        return True


if __name__ == "__main__":
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    WS_WIKI.login()
    with Ebooks(wiki=WS_WIKI, debug=False, log_to_screen=True, log_to_wiki=False) as bot:
        bot.run()
