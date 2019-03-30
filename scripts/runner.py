import codecs
import importlib
import inspect
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List

import git
from pywikibot import Site

from scripts.service.author_list import AuthorList
from scripts.service.gl.create_magazine import GlCreateMagazine
from scripts.service.gl.status import GlStatus
from scripts.service.ws_re.register_printer import ReRegisterPrinter
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
        path_for_creation = path_to_archive
        if not os.path.exists(path_for_creation):
            os.mkdir(path_for_creation)
            open(path_to_archive.joinpath("__init__.py"), "w").close()
        return path_to_archive

    def _get_files_to_run(self) -> List[str]:
        file_list = []
        for file_name in os.listdir(self.path_one_time):
            if not re.search("test", file_name):
                if os.path.isfile(self.path_one_time.joinpath(file_name)):
                    file_list.append(file_name)
        file_list.remove("__init__.py")
        self.logger.info(f"Files in one_time directory: {file_list}")
        return sorted(file_list)

    def _run_bot_from_file(self, file: str) -> bool:
        self.logger.info(f"Run {file}")
        onetime_module = \
            importlib.import_module(f"scripts.{self.folder_one_time}.{file.replace('.py', '')}")
        attributes = tuple(a for a in dir(onetime_module) if not a.startswith("__"))
        success = True
        for attribute in attributes:
            module_attr = getattr(onetime_module, attribute)
            if inspect.isclass(module_attr):
                if "OneTimeBot" in str(module_attr.__bases__):
                    success = \
                        self.run_bot(module_attr(wiki=self.wiki, debug=self.debug)) and success
        return success

    def _move_file_to_archive(self, file: str):
        os.rename(self.path_one_time.joinpath(file),
                  self.path_archive.joinpath(file))
        with open(self.path_archive.joinpath(file), "r+") as moved_bot_file:
            pretext = moved_bot_file.read()
            moved_bot_file.seek(0, 0)
            moved_bot_file.write(f"# successful processed on "
                                 f"{self.timestamp.start_of_run.strftime('%Y-%m-%d')}\n{pretext}")
        for file_name in os.listdir(self.path_one_time):
            if re.search(file.split(".")[0], file_name):
                os.rename(self.path_one_time.joinpath(file_name),
                          self.path_archive.joinpath(file_name))

    def _push_files(self, files: List[str]):
        repo = git.Repo(search_parent_directories=True)
        files_add = []
        files_remove = []
        for file in files:
            for file_name in os.listdir(self.path_archive):
                if re.search(file.split(".")[0], file_name):
                    files_add.append(self.path_archive.joinpath(file_name))
                    files_remove.append(self.path_one_time.joinpath(file_name))
        if files_add:
            repo.index.add(files_add)
        if files_remove:
            repo.index.remove(files_remove)
        repo.index.commit(f"move successful bot scripts: {', '.join(files)}")
        origin = repo.remote("origin")
        origin.push()

    def task(self):
        super().task()
        list_of_successful_files = []
        for file in self._get_files_to_run():
            if self._run_bot_from_file(file):
                self._move_file_to_archive(file)
                list_of_successful_files.append(file)
        if list_of_successful_files:
            self.logger.info(f"This files were successful: {list_of_successful_files}")
            self._push_files(list_of_successful_files)
        return True


if __name__ == "__main__":  # pragma: no cover
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    SCHEDULER = TheBotItScheduler(wiki=WS_WIKI, debug=False)
    SCHEDULER.daily_bots = [AuthorList, ReScanner, GlCreateMagazine, ReRegisterPrinter]
    SCHEDULER.weekly_bots = {0: [],  # monday
                             1: [],
                             2: [],
                             3: [],
                             4: [],
                             5: [],
                             6: [ReStatus]}  # sunday
    SCHEDULER.monthly_bots = {1: [GlStatus]}
    SCHEDULER.bots_on_last_day_of_month = []
    with SCHEDULER as bot:
        bot.run()
