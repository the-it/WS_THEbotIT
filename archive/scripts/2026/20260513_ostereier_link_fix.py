import re

from pywikibot import Site, Page

from tools.bots.cloud_bot import CloudBot
from tools.petscan import PetScan

OLD_LINK = "Ostereier für Buchhändler"
NEW_LINK = "Ostereier für Buchhändler (1863)"


class OstereierLinkFix(CloudBot):
    def task(self):
        searcher = PetScan()
        searcher.add_namespace("Seite")
        searcher.add_positive_category(OLD_LINK)
        lemma_list = searcher.run()
        self.logger.info(f"Found {len(lemma_list)} pages to check.")

        for lemma in lemma_list:
            page = Page(self.wiki, f"Seite:{lemma["title"]}")
            old_text = page.text
            new_text = re.sub(
                r"\[\[" + re.escape(OLD_LINK) + r"(?!\s*\()",
                f"[[{NEW_LINK}",
                old_text,
            )
            new_text = re.sub(
                r"\|" + re.escape(OLD_LINK) + r"(?!\s*\()",
                f"|{NEW_LINK}",
                new_text,
            )
            if new_text != old_text:
                page.text = new_text
                page.save(
                    summary=f"[[{OLD_LINK}]] → [[{NEW_LINK}]]",
                    botflag=True,
                )
                self.logger.info(f"Fixed: {lemma['title']}")
            else:
                self.logger.info(f"No change needed: {lemma['title']}")

        return True


if __name__ == "__main__":
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    WS_WIKI.login()
    with OstereierLinkFix(wiki=WS_WIKI, debug=False, log_to_screen=True, log_to_wiki=False) as bot:
        bot.run()
