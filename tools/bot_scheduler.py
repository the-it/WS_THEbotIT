from datetime import datetime, timedelta
from typing import Dict, Tuple

from pywikibot import Site

from tools.bots import BotException, CanonicalBot, OneTimeBot


class BotScheduler(CanonicalBot):
    def __init__(self, wiki: Site, debug: bool):
        self._daily_bots = None  # type: Tuple[type(CanonicalBot)]
        self._weekly_bots = None  # type: Dict[int, Tuple[type(CanonicalBot)]]
        self._monthly_bots = None  # type: Dict[int, Tuple[type(CanonicalBot)]]
        self._bots_on_last_day_of_month = None  # type: Tuple[type(CanonicalBot)]
        CanonicalBot.__init__(self, wiki, debug)
        self._now = datetime.now()

    def now(self) -> datetime:  # pragma: no cover
        return self._now

    def _last_day_of_month(self) -> bool:
        return (self.now() + timedelta(days=1)).day == 1

    @property
    def daily_bots(self) -> Tuple[type(CanonicalBot)]:
        return self._daily_bots

    @daily_bots.setter
    def daily_bots(self, new_config: Tuple[type(CanonicalBot)]):
        self._daily_bots = new_config

    @property
    def weekly_bots(self) -> Dict[int, Tuple[type(CanonicalBot)]]:
        return self._weekly_bots

    @weekly_bots.setter
    def weekly_bots(self, new_config: Dict[int, Tuple[type(CanonicalBot)]]):
        self._weekly_bots = new_config

    @property
    def monthly_bots(self) -> Dict[int, Tuple[type(CanonicalBot)]]:
        return self._monthly_bots

    @monthly_bots.setter
    def monthly_bots(self, new_config: Dict[int, Tuple[type(CanonicalBot)]]):
        self._monthly_bots = new_config

    @property
    def bots_on_last_day_of_month(self) -> Tuple[type(CanonicalBot)]:
        return self._bots_on_last_day_of_month

    @bots_on_last_day_of_month.setter
    def bots_on_last_day_of_month(self, new_config: Tuple[type(CanonicalBot)]):
        self._bots_on_last_day_of_month = new_config

    def run_bot(self, bot_to_run: OneTimeBot) -> bool:
        if not isinstance(bot_to_run, OneTimeBot):
            raise BotException("{} is not an instance of CanonicalBot or OneTimeBot"
                               .format(bot_to_run))
        self.logger.info("The bot {name} is scheduled for start.".format(name=bot_to_run.bot_name))
        with bot_to_run:
            success = bot_to_run.run()
        path_to_log = "{user}/Logs/{name}"\
            .format(name=bot_to_run.bot_name, user=self.wiki.username())
        self.logger.info("Log @ [https://de.wikisource.org/wiki/Benutzer:{link}#{headline} {link}]"
                         .format(link=path_to_log,
                                 headline=bot_to_run.timestamp.start_of_run
                                 .strftime("%y-%m-%d_%H:%M:%S")))
        if not success:
            self.logger.error("<span style=\"background:#FF0000\">"
                              "The bot {name} wasn't successful.</span>"
                              .format(name=bot_to_run.bot_name))
        return success

    def run_dailys(self):
        if self.daily_bots:
            for daily_bot in self.daily_bots:
                self.run_bot(daily_bot(wiki=self.wiki, debug=self.debug))

    def run_weeklys(self):
        if self.weekly_bots:
            try:
                for weekly_bot in self.weekly_bots[self.now().weekday()]:
                    self.run_bot(weekly_bot(wiki=self.wiki, debug=self.debug))
            except KeyError:
                pass

    def run_monthlys(self):
        if self.monthly_bots:
            try:
                for monthly_bot in self.monthly_bots[self.now().day]:
                    self.run_bot(monthly_bot(wiki=self.wiki, debug=self.debug))
            except KeyError:
                pass
        if self.bots_on_last_day_of_month:
            if self._last_day_of_month():
                for last_day_monthly_bot in self.bots_on_last_day_of_month:
                    self.run_bot(last_day_monthly_bot(wiki=self.wiki, debug=self.debug))

    def task(self):
        self.run_dailys()
        self.run_weeklys()
        self.run_monthlys()


if __name__ == "__main__":  # pragma: no cover
    WS_WIKI = Site(code='de', fam='wikisource', user='THEbotIT')
    BOT_SCHEDULER = BotScheduler(wiki=WS_WIKI, debug=True)

    class TestBot(OneTimeBot):
        def task(self):
            self.logger.info("TestBot")
            return True

    BOT_SCHEDULER.daily_bots = [TestBot]
    with BOT_SCHEDULER as bot:
        bot.run()
