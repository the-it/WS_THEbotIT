from typing import Optional, List

from pywikibot import Site, Page, User
from pywikibot.page import Revision

from tools.bots.pi import OneTimeBot


class RevertBotDeletions(OneTimeBot):
    def task(self):
        the_bot_it_user = User(self.wiki, "Benutzer:THEbotIT")
        page: Optional[Page] = None
        for page, revision_id, ts, _ in the_bot_it_user.contributions(total=1000):
            last_two_reivisions: List[Revision] = list(page.revisions())[:2]
            # make sure the last edit is the potential dangerous one
            if last_two_reivisions[0]["revid"] == revision_id:
                if last_two_reivisions[0]["size"] - last_two_reivisions[1]["size"] < 0:
                    if "RE:" in page.title():
                        print(page)
                        print("bad edit")
        print("end")


if __name__ == "__main__":
    WS_WIKI = Site(code="de", fam="wikisource", user="THE IT")
    with RevertBotDeletions(wiki=WS_WIKI, debug=True, log_to_screen=True, log_to_wiki=False) as bot:
        bot.run()
