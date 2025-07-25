from typing import Optional, List

from pywikibot import Site, Page, User, Timestamp
from pywikibot.page import Revision

from archive.service.pi import OneTimeBot


class RevertBotDeletions(OneTimeBot):
    def task(self):
        the_bot_it_user = User(self.wiki, "Benutzer:THEbotIT")
        page: Optional[Page] = None
        for idx, (page, revision_id, ts, _) in enumerate(the_bot_it_user.contributions(total=10000, start=Timestamp(year=2022, month=3, day=26), end=Timestamp(year=2022, month=3, day=22))):
            if idx % 100 == 0:
                self.logger.info(f"index is {idx}")
            if idx < 700:
                continue
            last_two_reivisions: List[Revision] = list(page.revisions())[:2]
            # make sure the last edit is the potential dangerous one
            if last_two_reivisions[0]["revid"] == revision_id:
                if last_two_reivisions[0]["size"] - last_two_reivisions[1]["size"] < 0:
                    if "RE:" in page.title():
                        self.logger.info(f"bad edit on {page.title()}")
                        page.text = page.getOldVersion(oldid=last_two_reivisions[1]["revid"])
                        page.save(f"Änderung {last_two_reivisions[0]['revid']} von [[Benutzer:THEbotIT|THEbotIT]] ([[Benutzer Diskussion:THEbotIT|Diskussion]]) rückgängig gemacht.")
        self.logger.info("THE END")


if __name__ == "__main__":
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    with RevertBotDeletions(wiki=WS_WIKI, debug=True, log_to_screen=True, log_to_wiki=False) as bot:
        bot.run()
