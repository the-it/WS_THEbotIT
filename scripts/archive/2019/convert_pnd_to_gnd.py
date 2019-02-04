# successful processed on 2019-02-04
import re

from pywikibot import Site, Page

from tools.bots import OneTimeBot
from tools.petscan import PetScan


class ConvertPndToGnd(OneTimeBot):
    def task(self):  # pragma: no cover
        regex = re.compile(r"\n\|PND=")
        searcher = PetScan()
        searcher.add_yes_template("ADBDaten")
        searcher.add_positive_category("ADB:Ohne GND-Link")
        lemma_list = searcher.run()
        for lemma in lemma_list:
            page = Page(self.wiki, lemma["title"])
            temp_text = page.text
            if regex.search(temp_text):
                self.logger.info("change {}".format(lemma["title"]))
                temp_text = regex.sub("\n|GND=", temp_text)
            page.text = temp_text
            page.save("PND -> GND", botflag=True)
        return True


if __name__ == "__main__":  # pragma: no cover
    WIKI = Site(code='de', fam='wikisource', user='THEbotIT')
    with ConvertPndToGnd(wiki=WIKI, debug=True) as bot:
        bot.run()
