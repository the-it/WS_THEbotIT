from datetime import datetime, timedelta
from typing import Dict, Tuple

from pywikibot import Site

from tools.bots import CanonicalBot, OneTimeBot


class BotScheduler(CanonicalBot):
    def __init__(self, wiki: Site, debug: bool):
        self._run_daily = None
        self._run_weekly = None
        self._run_monthly = None
        self._run_on_last_day_of_month = None
        self._run_one_time = None
        CanonicalBot.__init__(self, wiki, debug)
        self._now = datetime.now()

    def now(self) -> datetime:
        return self._now

    def _last_day_of_month(self) -> bool:
        return (self.now() + timedelta(days=1)).day == 1

    @property
    def run_daily(self) -> Tuple[type(CanonicalBot)]:
        return self._run_daily

    @run_daily.setter
    def run_daily(self, new_config: Tuple[type(CanonicalBot)]):
        self._run_daily = new_config

    @property
    def run_weekly(self) -> Dict[int, Tuple[type(CanonicalBot)]]:
        return self._run_weekly

    @run_weekly.setter
    def run_weekly(self, new_config: Dict[int, Tuple[type(CanonicalBot)]]):
        self._run_weekly = new_config

    @property
    def run_monthly(self) -> Dict[int, Tuple[type(CanonicalBot)]]:
        return self._run_monthly

    @run_monthly.setter
    def run_monthly(self, new_config: Dict[int, Tuple[type(CanonicalBot)]]):
        self._run_daily = new_config

    @property
    def run_on_last_day_of_month(self) -> Tuple[type(CanonicalBot)]:
        return self._run_on_last_day_of_month

    @run_on_last_day_of_month.setter
    def run_on_last_day_of_month(self, new_config: Tuple[type(CanonicalBot)]):
        self._run_on_last_day_of_month = new_config

    @property
    def run_one_time(self) -> Tuple[str, str]:
        return self._run_one_time

    @run_one_time.setter
    def run_one_time(self, new_config: Tuple[str, str]):
        self._run_one_time = new_config

    def run_bot(self, bot_to_run: OneTimeBot) -> bool:
        self.logger.info("The bot {name} is scheduled for start.".format(name=bot_to_run.bot_name))
        with bot_to_run:
            success = bot_to_run.run()
        return success

    def task(self):
        pass
