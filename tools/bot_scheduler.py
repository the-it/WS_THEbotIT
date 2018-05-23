from datetime import datetime, timedelta
from typing import Dict, Tuple

from pywikibot import Site

from tools.bots import CanonicalBot, OneTimeBot, BotExeption


class BotScheduler(CanonicalBot):
    def __init__(self, wiki: Site, debug: bool):
        self._daily_bots = None
        self._weekly_bots = None
        self._monthly_bots = None
        self._bots_on_last_day_of_month = None
        self._bots_one_time = None
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

    @property
    def run_one_time(self) -> Tuple[str, str]:
        return self._bots_one_time

    @run_one_time.setter
    def run_one_time(self, new_config: Tuple[str, str]):
        self._bots_one_time = new_config

    def run_bot(self, bot_to_run: OneTimeBot) -> bool:
        if not isinstance(bot_to_run, OneTimeBot):
            raise BotExeption("{} is not an instance of OneTimeBot".format(bot_to_run))
        self.logger.info("The bot {name} is scheduled for start.".format(name=bot_to_run.bot_name))
        with bot_to_run:
            success = bot_to_run.run()
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

    # def run_one_timers(self):
    #     path_to_online = os.sep.join(["/home", "pi", "WS_THEbotIT", "scripts", "online"])
    #     one_timers = \
    #        tuple(file for file in os.listdir(path_to_online) if self.regex_one_timer.search(file))
    #     self.logger.info('One timers to run: {}'.format(one_timers))
    #     for one_timer in one_timers:
    #         self.logger.info('Run {}'.format(one_timer))
    #         onetime_module = \
    #             importlib.import_module('online.{}'.format(one_timer.replace('.py', '')))
    #         attributes = tuple(a for a in dir(onetime_module) if not a.startswith('__'))
    #         success = False
    #         for attribute in attributes:
    #             module_attr = getattr(onetime_module, attribute)
    #             if inspect.isclass(module_attr):
    #                 if 'OneTimeBot' in str(module_attr.__bases__):
    #                     with module_attr(wiki=self.wiki, debug=self.debug) as onetime_bot:
    #                         success = self.run_bot(onetime_bot)
    #         if success:
    #             # move the file to the archives if it was successful
    #             self.logger.info('{} finished the work successful'.format(one_timer))
    #             year = self.regex_one_timer.match(one_timer).group(1)
    #             os.rename(path_to_online + os.sep + one_timer,
    #                       path_to_online + os.sep + year + os.sep + one_timer)
    #             repo = git.Repo(search_parent_directories=True)
    #             repo.index.add([path_to_online + os.sep + year + os.sep + one_timer])
    #             repo.index.remove([path_to_online + os.sep + one_timer])
    #             repo.index.commit('move successful bot script')
    #             origin = repo.remote('origin')
    #             origin.push()
