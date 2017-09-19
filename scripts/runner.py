import calendar
import importlib
import inspect
import os
import re
import sys
from datetime import datetime
import git

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + os.sep + os.pardir + os.sep)

from pywikibot import Site
from scripts.service.author_list import AuthorList
from scripts.service.re.status import ReStatus
from scripts.service.gl.status import GlStatus
from scripts.service.gl.create_magazine import GlCreateMagazine
from scripts.service.re.scanner import ReScanner
from tools.bots import SaveExecution, CanonicalBot, OneTimeBot


class DailyRunner(CanonicalBot):
    def __init__(self, wiki, debug):
        CanonicalBot.__init__(self, wiki, debug)
        self.bot_name = 'DailyRunner'
        self.now = datetime.now()
        self.regex_one_timer = re.compile('(\d{4})\d{4}')

    def run(self):
        one_timers = tuple(file for file in os.listdir('online') if self.regex_one_timer.search(file))
        self.logger.info('One timers to run: {}'.format(one_timers))
        for one_timer in one_timers:
            self.logger.info('Run {}'.format(one_timer))
            module = importlib.import_module('online.{}'.format(one_timer.replace('.py', '')))
            attributes = tuple(a for a in dir(module) if not a.startswith('__'))
            success = False
            for attribute in attributes:
                object = getattr(module, attribute)
                if inspect.isclass(object):
                    if 'OneTimeBot' in str(object.__bases__):
                        with SaveExecution(object(wiki=self.wiki, debug=self.debug)) as bot:
                            success = bot.run()
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
        for bot in daily_list:
            self.run_bot(bot(wiki=self.wiki, debug=False))

    def run_weeklys(self):
        weekly_list = {0: [],  # monday
                       1: [],
                       2: [],
                       3: [],
                       4: [],
                       5: [GlCreateMagazine],
                       6: [ReStatus]}  # sunday
        for bot in weekly_list[self.now.weekday()]:
            self.run_bot(bot(wiki=self.wiki, debug=False))

    def run_monthly(self):
        monthly_list = {1: [GlStatus]}
        last_day_of_month = []
        try:
            for bot in monthly_list[self.now.day]:
                self.run_bot(bot(wiki=self.wiki, debug=False))
        except KeyError:
            pass

        # last day of the month
        if self.now.day == calendar.monthrange(self.now.year, self.now.month)[1]:
            for bot in last_day_of_month:
                self.run_bot(bot(wiki=self.wiki, debug=False))

    def run_bot(self, bot):
        with SaveExecution(bot) as bot:
            bot.run()


if __name__ == "__main__":
    wiki = Site(code='de', fam='wikisource', user='THEbotIT')

    with SaveExecution(DailyRunner(wiki=wiki, debug=True)) as bot:
        bot.run()



