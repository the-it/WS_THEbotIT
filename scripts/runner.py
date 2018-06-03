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

if datetime.now() > datetime(year=2020, month=9, day=13):  # pragma: no cover
    raise DeprecationWarning("Python 3.5 has reached end of live. "
                             "Consider removing all the casts Path -> str.")


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
        path_for_creation = str(path_to_archive)
        if not os.path.exists(path_for_creation):
            os.mkdir(path_for_creation)
            open(str(path_to_archive.joinpath("__init__.py")), "w").close()
        return path_to_archive

    def _get_files_to_run(self) -> List[str]:
        file_list = [file for file in os.listdir(str(self.path_one_time))
                     if os.path.isfile(str(self.path_one_time.joinpath(file)))]
        file_list.remove("__init__.py")
        self.logger.info("Files in one_time directory: {}".format(file_list))
        return sorted(file_list)

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
        if list_of_successful_files:
            self.logger.info("This files were successful: {}".format(list_of_successful_files))
            self._push_files(list_of_successful_files)
        return True


if __name__ == "__main__":  # pragma: no cover
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    WS_WIKI = Site(code='de', fam='wikisource', user='THEbotIT')
    SCHEDULER = TheBotItScheduler(wiki=WS_WIKI, debug=False)
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
