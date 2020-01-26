from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from pywikibot import Site, Page

from tools.bots.cloud.logger import WikiLogger
from tools.bots.cloud.persisted_data import PersistedData
from tools.bots.cloud.status_manager import StatusManager


class LambdaBot(ABC):
    def __init__(self, wiki: Site = None, debug: bool = True, log_to_screen: bool = True, log_to_wiki: bool = True):
        self.success: bool = False
        self.log_to_screen: bool = log_to_screen
        self.log_to_wiki: bool = log_to_wiki
        self.status: StatusManager = StatusManager(bot_name=self.bot_name)
        self.data: PersistedData = PersistedData(bot_name=self.bot_name)
        self.wiki: Page = wiki
        self.debug: bool = debug
        self.timeout: timedelta = timedelta(days=1)
        self.logger: WikiLogger = WikiLogger(self.bot_name,
                                             self.status.current_run.start_time,
                                             log_to_screen=self.log_to_screen)
        self.new_data_model = datetime.min

    def __enter__(self):
        # self.timestamp.__enter__()
        self.logger.__enter__()
        self.logger.info(f"Start the bot {self.bot_name}.")
        self._load_data()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._dump_data()
        self.status.finish_run(self.success)
        self.logger.info(f"Finish bot {self.bot_name} in "
                         f"{datetime.now() - self.status.current_run.start_time}.")
        if self.log_to_wiki:
            self.send_log_to_wiki()
        self.logger.__exit__(exc_type, exc_val, exc_tb)

    def _load_data(self):
        if not self.status.last_run or not self.status.last_run.success:
            self.data.assign_dict({})
            self.logger.warning("The last run wasn\'t successful. The data is thrown away.")
        elif self.data_outdated():
            self.data.assign_dict({})
            self.logger.warning("The data is thrown away. It is out of date")
        else:
            self.data.load()

    def _dump_data(self):
        if self.success:
            self.data.dump(success=True)
        else:
            self.data.dump(success=False)
            self.logger.critical("There was an error in the general procedure. "
                                 "The broken data and a backup of the old will be keept.")

    @abstractmethod
    def task(self) -> bool:
        pass

    @classmethod
    def get_bot_name(cls) -> str:
        return cls.__name__

    @property
    def bot_name(self) -> str:
        return self.get_bot_name()

    def run(self) -> bool:
        try:
            self.success = bool(self.task())  # pylint: disable=not-callable
        except Exception as catched_exception:  # pylint: disable=broad-except
            self.logger.exception("Logging an uncaught exception", exc_info=catched_exception)
            self.success = False
        return self.success

    def _watchdog(self) -> bool:
        time_over: bool = False
        if self.timeout:
            diff = datetime.now() - self.status.current_run.start_time
            if diff > self.timeout:
                self.logger.warning("Bot finished by timeout.")
                time_over = True
        return time_over

    def send_log_to_wiki(self):
        wiki_log_page = f"Benutzer:THEbotIT/Logs/{self.bot_name}"
        page = Page(self.wiki, wiki_log_page)
        page.text += self.logger.create_wiki_log_lines()
        page.save(f"Update of Bot {self.bot_name}", botflag=True)

    @staticmethod
    def save_if_changed(page: Page, text: str, change_msg: str):
        if text.rstrip() != page.text:
            page.text = text
            page.save(change_msg, botflag=True)

    def data_outdated(self) -> bool:
        outdated = False
        if not self.status.last_successful_run:
            outdated = True
        elif self.status.last_successful_run.start_time < self.new_data_model:
            outdated = True
        return outdated

    def create_timestamp_for_search(self, offset: timedelta = timedelta(seconds=0)) -> datetime:
        if self.status.last_run and self.status.last_run.success:
            return self.status.last_run.start_time - offset
        return datetime.min
