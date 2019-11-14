import contextlib
import sys
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Type

from pywikibot import Site

from tools.bots import BotException, CanonicalBot, OneTimeBot

BotList = Optional[List[Type[CanonicalBot]]]


class BotScheduler(CanonicalBot):
    def __init__(self, wiki: Site, debug: bool):
        self._daily_bots: BotList = []
        self._weekly_bots: Dict[int, BotList] = {}
        self._monthly_bots: Dict[int, BotList] = {}
        self._bots_on_last_day_of_month: BotList = []
        CanonicalBot.__init__(self, wiki, debug)
        self._now = datetime.now()

    def now(self) -> datetime:  # pragma: no cover
        return self._now

    def _last_day_of_month(self) -> bool:
        return (self.now() + timedelta(days=1)).day == 1

    @property
    def daily_bots(self) -> BotList:
        return self._daily_bots

    @daily_bots.setter
    def daily_bots(self, new_config: BotList):
        self._daily_bots = new_config

    @property
    def weekly_bots(self) -> Dict[int, BotList]:
        return self._weekly_bots

    @weekly_bots.setter
    def weekly_bots(self, new_config: Dict[int, BotList]):
        self._weekly_bots = new_config

    @property
    def monthly_bots(self) -> Dict[int, BotList]:
        return self._monthly_bots

    @monthly_bots.setter
    def monthly_bots(self, new_config: Dict[int, BotList]):
        self._monthly_bots = new_config

    @property
    def bots_on_last_day_of_month(self) -> BotList:
        return self._bots_on_last_day_of_month

    @bots_on_last_day_of_month.setter
    def bots_on_last_day_of_month(self, new_config: BotList):
        self._bots_on_last_day_of_month = new_config

    def run_bot(self, bot_to_run: OneTimeBot) -> bool:
        if not isinstance(bot_to_run, OneTimeBot):
            raise BotException(f"{bot_to_run} is not an instance of CanonicalBot or OneTimeBot")
        self.logger.info(f"The bot {bot_to_run.bot_name} is scheduled for start.")
        with bot_to_run:
            success = bot_to_run.run()
        path_to_log = f"{self.wiki.username()}/Logs/{bot_to_run.bot_name}"
        self.logger.info(f"Log @ [https://de.wikisource.org/wiki/Benutzer:{path_to_log}"
                         f"#{bot_to_run.timestamp.start_of_run:%y-%m-%d_%H:%M:%S} {path_to_log}]")
        if not success:
            self.logger.error(f"<span style=\"background:#FF0000\">"
                              f"The bot {bot_to_run.bot_name} wasn't successful.</span>")
        return success

    def run_dailys(self):
        if self.daily_bots:
            for daily_bot in self.daily_bots:
                self.run_bot(daily_bot(wiki=self.wiki, debug=self.debug))

    def run_weeklys(self):
        if self.weekly_bots:
            with contextlib.suppress(KeyError):
                for weekly_bot in self.weekly_bots[self.now().weekday()]:
                    self.run_bot(weekly_bot(wiki=self.wiki, debug=self.debug))

    def run_monthlys(self):
        if self.monthly_bots:
            with contextlib.suppress(KeyError):
                for monthly_bot in self.monthly_bots[self.now().day]:
                    self.run_bot(monthly_bot(wiki=self.wiki, debug=self.debug))
        if self.bots_on_last_day_of_month:
            if self._last_day_of_month():
                for last_day_monthly_bot in self.bots_on_last_day_of_month:
                    self.run_bot(last_day_monthly_bot(wiki=self.wiki, debug=self.debug))

    def task(self):
        self.logger.info(f"Running on Python Version: {sys.version}")
        self.run_dailys()
        self.run_weeklys()
        self.run_monthlys()


if __name__ == "__main__":  # pragma: no cover
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    BOT_SCHEDULER = BotScheduler(wiki=WS_WIKI, debug=True)

    class TestBot(CanonicalBot):
        def task(self):
            self.logger.info("TestBot")
            return True

    BOT_SCHEDULER.daily_bots = [TestBot]
    with BOT_SCHEDULER as bot:
        bot.run()
