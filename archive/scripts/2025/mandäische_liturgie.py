import re

from pywikibot import Site, Page

from tools.bots.cloud_bot import CloudBot


class Liturgie(CloudBot):
    def task(self):
        for i in range(47, 104):
            page = Page(self.wiki, f"Mandäische Liturgien/Qolasta/{i}")
            page.delete("stattgegebener [[Wikisource:Löschkandidaten|Löschantrag]]")


if __name__ == "__main__":
    WS_WIKI = Site(code="de", fam="wikisource", user="THE IT")
    WS_WIKI.login()
    with Liturgie(wiki=WS_WIKI, debug=False, log_to_screen=True, log_to_wiki=False) as bot:
        bot.run()
