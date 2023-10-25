import json

from pywikibot import Site, Page

from tools.bots.pi import OneTimeBot


class PageRedirects(OneTimeBot):
    def task(self):
        try:
            with open("page_redirects.json") as json_file:
                lemma_dict = json.load(json_file)
        except IOError:
            exit(1)
        for lemma in lemma_dict["rows"]:
            lemma_page = Page(self.wiki, lemma[0])
            lemma_page.delete("unnötige Weiterleitung", prompt=False, mark=True)


if __name__ == "__main__":
    WS_WIKI = Site(code="de", fam="wikisource", user="THE IT")
    with PageRedirects(wiki=WS_WIKI, debug=False, log_to_screen=False, log_to_wiki=False) as bot:
        bot.run()
