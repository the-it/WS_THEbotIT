import calendar
import codecs
import importlib
import inspect
import os
import re
import sys
from datetime import datetime
import git
from pywikibot import Site

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + os.sep + os.pardir + os.sep)

from scripts.service.author_list import AuthorList
from scripts.service.re.status import ReStatus
from scripts.service.gl.status import GlStatus
from scripts.service.gl.create_magazine import GlCreateMagazine
from scripts.service.re.scanner import ReScanner
from tools.bots import CanonicalBot

sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())


class DailyRunner(CanonicalBot):
    bot_name = 'DailyRunner'

    def __init__(self, wiki, debug):
        CanonicalBot.__init__(self, wiki, debug)

        self.now = datetime.now()
        self.regex_one_timer = re.compile('(\d{4})\d{4}')

    def run_one_timers(self):
        one_timers = tuple(file for file in os.listdir('online') if self.regex_one_timer.search(file))
        self.logger.info('One timers to run: {}'.format(one_timers))
        for one_timer in one_timers:
            self.logger.info('Run {}'.format(one_timer))
            onetime_module = importlib.import_module('online.{}'.format(one_timer.replace('.py', '')))
            attributes = tuple(a for a in dir(onetime_module) if not a.startswith('__'))
            success = False
            for attribute in attributes:
                module_attr = getattr(onetime_module, attribute)
                if inspect.isclass(module_attr):
                    if 'OneTimeBot' in str(module_attr.__bases__):
                        with module_attr(wiki=self.wiki, debug=self.debug) as onetime_bot:
                            success = self.run_bot(onetime_bot)
            if success:
                # move the file to the archives if it was successful
                self.logger.info('{} finished the work successful'.format(one_timer))
                year = self.regex_one_timer.match(one_timer).group(1)
                os.rename('online' + os.sep + one_timer, 'online' + os.sep + year + os.sep + one_timer)
                repo = git.Repo(search_parent_directories=True)
                repo.index.add(['scripts' + os.sep + 'online' + os.sep + year + os.sep + one_timer])
                repo.index.remove(['scripts' + os.sep + 'online' + os.sep + one_timer])
                repo.index.commit('move successful bot script')
                origin = repo.remote('origin')
                origin.push()

    def run_dailys(self):
        daily_list = [AuthorList, ReScanner]
        for daily_bot in daily_list:
            self.run_bot(daily_bot(wiki=self.wiki, debug=self.debug))

    def run_weeklys(self):
        weekly_list = {0: [],  # monday
                       1: [],
                       2: [],
                       3: [],
                       4: [],
                       5: [GlCreateMagazine],
                       6: [ReStatus]}  # sunday
        for weekly_bot in weekly_list[self.now.weekday()]:
            self.run_bot(weekly_bot(wiki=self.wiki, debug=self.debug))

    def run_monthly(self):
        monthly_list = {1: [GlStatus]}
        last_day_of_month = []
        try:
            for monthly_bot in monthly_list[self.now.day]:
                self.run_bot(monthly_bot(wiki=self.wiki, debug=self.debug))
        except KeyError:
            pass

        # last day of the month
        if self.now.day == calendar.monthrange(self.now.year, self.now.month)[1]:
            for last_day_monthly_bot in last_day_of_month:
                self.run_bot(last_day_monthly_bot(wiki=self.wiki, debug=self.debug))

    def run_bot(self, bot_to_run):
        self.logger.info("The bot {name} is scheduled for start.".format(name=bot_to_run.bot_name))
        try:
            success = bot_to_run.run()
        except Exception as e:
            self.logger.exception("The bot {name} encountered an exception."
                                  .format(name=bot_to_run.bot_name),
                                  exc_info=e)
            success = False
        return success

    def task(self):
        self.run_dailys()
        self.run_weeklys()
        self.run_monthly()
        self.run_one_timers()
        return True


if __name__ == "__main__":
    wiki = Site(code='de', fam='wikisource', user='THEbotIT')
    with DailyRunner(wiki=wiki, debug=False) as bot:
        bot.run()
