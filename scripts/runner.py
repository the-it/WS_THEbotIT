import codecs
from datetime import datetime
import importlib
import inspect
import os
from pathlib import Path
import sys
from typing import List

import git
from pywikibot import Site

from scripts.service.author_list import AuthorList
from scripts.service.gl.create_magazine import GlCreateMagazine
from scripts.service.gl.status import GlStatus
from scripts.service.little_tasks.hilbert_timer import HilbertTimer
from scripts.service.ws_re.scanner import ReScanner
from scripts.service.ws_re.status import ReStatus
from tools.bot_scheduler import BotScheduler


class TheBotItScheduler(BotScheduler):
    folder_one_time = "one_time_run"
    folder_archive = "archive"

    @property
    def path_one_time(self) -> Path:
        return Path(__file__).parent.joinpath(self.folder_one_time)

    @property
    def path_archive(self) -> Path:
        path_to_archive = Path(__file__)\
            .parent\
            .joinpath(self.folder_archive)\
            .joinpath(str(datetime.today().year))
        if not os.path.exists(path_to_archive):
            os.mkdir(path_to_archive)
        return path_to_archive

    def _get_files_to_run(self) -> List[str]:
        file_list = os.listdir(str(self.path_one_time))
        file_list.remove("init.py")
        return file_list

    def _run_bot_from_file(self, file: str) -> bool:
        self.logger.info('Run {}'.format(file))
        onetime_module = \
            importlib.import_module('scripts.{}.{}'
                                    .format(self.folder_one_time, file.replace('.py', '')))
        attributes = tuple(a for a in dir(onetime_module) if not a.startswith('__'))
        success = True
        for attribute in attributes:
            module_attr = getattr(onetime_module, attribute)
            if inspect.isclass(module_attr):
                if 'OneTimeBot' in str(module_attr.__bases__):
                    success = \
                        self.run_bot(module_attr(wiki=self.wiki, debug=self.debug)) and success
        return success

    def _move_file_to_archive(self, file: str):
        os.rename(str(self.path_one_time.joinpath(file)), str(self.path_archive.joinpath(file)))
        with open(str(self.path_archive.joinpath(file)), "r+") as moved_bot_file:
            pretext = moved_bot_file.read()
            moved_bot_file.seek(0, 0)
            moved_bot_file.write("# successful processed on {}\n{}"
                                 .format(self.timestamp.start_of_run.strftime("%Y-%m-%d"), pretext))

    def _push_files(self, files: List[str]):
        repo = git.Repo(search_parent_directories=True)
        files_to_add = [str(self.path_archive.joinpath(file)) for file in files]
        repo.index.add(files_to_add)
        files_to_remove = [str(self.path_one_time.joinpath(file)) for file in files]
        repo.index.remove(files_to_remove)
        repo.index.commit('move successful bot scripts: {}'.format(", ".join(files)))
        origin = repo.remote('origin')
        origin.push()

    def task(self):
        super().task()
        list_of_successful_files = []
        for file in self._get_files_to_run():
            if self._run_bot_from_file(file):
                self._move_file_to_archive(file)
                list_of_successful_files.append(file)
        self._push_files(list_of_successful_files)

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


if __name__ == "__main__":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    WS_WIKI = Site(code='de', fam='wikisource', user='THEbotIT')
    SCHEDULER = BotScheduler(wiki=WS_WIKI, debug=False)
    SCHEDULER.daily_bots = [AuthorList, ReScanner]
    SCHEDULER.weekly_bots = {0: [],  # monday
                             1: [],
                             2: [],
                             3: [],
                             4: [],
                             5: [],
                             6: [ReStatus, GlCreateMagazine, HilbertTimer]}  # sunday
    SCHEDULER.monthly_bots = {1: [GlStatus]}
    SCHEDULER.bots_on_last_day_of_month = []
    with SCHEDULER as bot:
        bot.run()
