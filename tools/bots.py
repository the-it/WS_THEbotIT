import json
import logging
import os
import sys
from abc import abstractmethod, ABC
from collections.abc import Mapping
from datetime import datetime, timedelta
from typing import Dict, Any, Iterator
from typing import TypedDict  # pylint: disable=no-name-in-module

from pywikibot import Page, Site


# type hints
class LoggerNameDict(TypedDict):
    info: str
    debug: str

class LastRunDict(TypedDict):
    success: bool
    timestamp: str


class BotException(Exception):
    pass


_DATA_PATH: str = os.path.expanduser("~") + os.sep + ".wiki_bot"


def _get_data_path() -> str:
    if not os.path.exists(_DATA_PATH):
        os.mkdir(_DATA_PATH)
    return _DATA_PATH


class WikiLogger():
    _logger_format: str = "[%(asctime)s] [%(levelname)-8s] [%(message)s]"
    _logger_date_format: str = "%H:%M:%S"
    _wiki_timestamp_format: str = "%y-%m-%d_%H:%M:%S"

    def __init__(self, bot_name: str, start_time: datetime, log_to_screen: bool = True):
        self._bot_name: str = bot_name
        self._start_time: datetime = start_time
        self._data_path: str = _get_data_path()
        self._logger: logging.Logger = logging.getLogger(self._bot_name)
        self._logger_names: LoggerNameDict = self._get_logger_names()
        self._log_to_screen: bool = log_to_screen

    def __enter__(self):
        self._setup_logger_properties()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.tear_down()

    def tear_down(self):
        for handler in self._logger.handlers[:]:
            handler.close()
            self._logger.removeHandler(handler)
        if os.path.isfile(self._data_path + os.sep + self._logger_names["info"]):
            os.remove(self._data_path + os.sep + self._logger_names["info"])
        sys.stdout.flush()
        logging.shutdown()

    def _get_logger_names(self) -> LoggerNameDict:
        start_time = self._start_time.strftime('%y%m%d%H%M%S')
        return {"info": f"{self._bot_name}_INFO_{start_time}.log",
                "debug": f"{self._bot_name}_DEBUG_{start_time}.log"}

    def _setup_logger_properties(self):
        self._logger.setLevel(logging.DEBUG)
        error_log = logging.FileHandler(self._data_path + os.sep + self._logger_names["info"],
                                        encoding="utf8")
        error_log.setLevel(logging.INFO)
        debug_log = logging.FileHandler(self._data_path + os.sep + self._logger_names["debug"],
                                        encoding="utf8")
        debug_log.setLevel(logging.DEBUG)
        formatter = logging.Formatter(self._logger_format, datefmt=self._logger_date_format)
        error_log.setFormatter(formatter)
        debug_log.setFormatter(formatter)
        self._logger.addHandler(error_log)
        self._logger.addHandler(debug_log)
        if self._log_to_screen:  # pragma: no cover
            # this activates the output of the logger
            debug_stream = logging.StreamHandler(sys.stdout)
            debug_stream.setLevel(logging.DEBUG)
            debug_stream.setFormatter(formatter)
            self._logger.addHandler(debug_stream)

    def debug(self, msg: str):
        self._logger.log(logging.DEBUG, msg)

    def info(self, msg: str):
        self._logger.log(logging.INFO, msg)

    def warning(self, msg: str):
        self._logger.log(logging.WARNING, msg)

    def error(self, msg: str):
        self._logger.log(logging.ERROR, msg)

    def critical(self, msg: str):
        self._logger.log(logging.CRITICAL, msg)

    def exception(self, msg: str, exc_info):
        self._logger.exception(msg=msg, exc_info=exc_info)

    def create_wiki_log_lines(self) -> str:
        with open(self._data_path + os.sep + self._logger_names["info"], encoding="utf8") as filepointer:
            line_list = list()
            for line in filepointer:
                line_list.append(line.strip())
            log_lines = ""
            log_lines = log_lines \
                + "\n\n" \
                + f"=={self._start_time.strftime(self._wiki_timestamp_format)}==" \
                + "\n\n" \
                + "\n\n".join(line_list) \
                + "\n--~~~~"
            return log_lines


class PersistedTimestamp():
    _timeformat: str = "%Y-%m-%d_%H:%M:%S"

    def __init__(self, bot_name: str):
        self._last_run: datetime = datetime.utcfromtimestamp(0)
        self._success_last_run: bool = False
        self._success_this_run: bool = False
        self._start: datetime = datetime.now()
        self._data_path: str = _get_data_path()
        self._full_filename: str = self._data_path + os.sep + f"{bot_name}.last_run.json"

    def __enter__(self):
        self.set_up()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.tear_down()

    def set_up(self):
        try:
            with open(self._full_filename, mode="r") as persist_json:
                last_run_dict: LastRunDict = json.load(persist_json)
                self._last_run = datetime.strptime(last_run_dict["timestamp"], self._timeformat)
                self._success_last_run = last_run_dict["success"]
            os.remove(self._full_filename)
        except FileNotFoundError:
            pass

    def tear_down(self):
        with open(self._full_filename, mode="w") as persist_json:
            json.dump({"timestamp": self._start.strftime(self._timeformat), "success": self.success_this_run},
                      persist_json)

    @property
    def last_run(self):
        return self._last_run

    @last_run.setter
    def last_run(self, value):
        # todo: this is wrong ... defintive wrong
        if value is None:
            self._last_run = value

    @property
    def start_of_run(self) -> datetime:
        return self._start

    @property
    def success_last_run(self) -> bool:
        return self._success_last_run

    @property
    def success_this_run(self) -> bool:
        return self._success_this_run

    @success_this_run.setter
    def success_this_run(self, new_value: bool):
        if isinstance(new_value, bool):
            self._success_this_run = new_value
        else:
            raise TypeError("success_this_run is a boolean value.")


class OneTimeBot(ABC):
    def __init__(self, wiki: Site = None, debug: bool = True,
                 log_to_screen: bool = True, log_to_wiki: bool = True):
        self.success: bool = False
        self.log_to_screen: bool = log_to_screen
        self.log_to_wiki: bool = log_to_wiki
        if not self.task:
            raise NotImplementedError("The class function \"task\" must be implemented!\n"
                                      "Example:\n"
                                      "class DoSomethingBot(OneTimeBot):\n"
                                      "    def task(self):\n"
                                      "        do_stuff()")
        self.timestamp: PersistedTimestamp = PersistedTimestamp(bot_name=self.bot_name)
        self.wiki: Page = wiki
        self.debug: bool = debug
        self.timeout: timedelta = timedelta(days=1)
        self.logger: WikiLogger = WikiLogger(self.bot_name,
                                             self.timestamp.start_of_run,
                                             log_to_screen=self.log_to_screen)

    def __enter__(self):
        self.timestamp.__enter__()
        self.logger.__enter__()
        self.logger.info(f"Start the bot {self.bot_name}.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.timestamp.success_this_run = self.success
        self.timestamp.__exit__(exc_type, exc_val, exc_tb)
        self.logger.info(f"Finish bot {self.bot_name} in "
                         f"{datetime.now() - self.timestamp.start_of_run}.")
        if self.log_to_wiki:
            self.send_log_to_wiki()
        self.logger.__exit__(exc_type, exc_val, exc_tb)

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
            diff = datetime.now() - self.timestamp.start_of_run
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


class PersistedData(Mapping):
    def __init__(self, bot_name: str):
        self._data: Dict = {}
        self.bot_name: str = bot_name
        self.data_folder: str = _get_data_path()
        self.file_name: str = self.data_folder + os.sep + bot_name + ".data.json"

    def __getitem__(self, item) -> Any:
        return self._data[item]

    def __setitem__(self, key: str, value: Any):
        self._data[key] = value

    def __delitem__(self, key: str):
        del self._data[key]

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterator:
        return iter(self._data)

    def assign_dict(self, new_dict: Dict):
        if isinstance(new_dict, dict):
            self._data = new_dict
        else:
            raise BotException(f"{new_dict} has the wrong type. It must be a dictionary.")

    def dump(self, success: bool = True):
        if success:
            with open(self.file_name, mode="w") as json_file:
                json.dump(self._data, json_file, indent=2)
            if os.path.isfile(self.file_name + ".deprecated"):
                os.remove(self.file_name + ".deprecated")
        else:
            with open(self.file_name + ".broken", mode="w") as json_file:
                json.dump(self._data, json_file, indent=2)

    def load(self):
        if os.path.exists(self.file_name):
            with open(self.file_name, mode="r") as json_file:
                self._data = json.load(json_file)
            os.rename(self.file_name, self.file_name + ".deprecated")
        else:
            raise BotException("No data to load.")

    def update(self, dict_to_update: Dict):
        self._data.update(dict_to_update)

    def _recover_data(self, type_of_data: str):
        try:
            with open(f"{self.file_name}.{type_of_data}", mode="r") as json_file:
                self.assign_dict(json.load(json_file))
        except FileNotFoundError:
            raise BotException(f"There is no {type_of_data} data to load.")

    def get_broken(self):
        self._recover_data("broken")

    def get_deprecated(self):
        self._recover_data("deprecated")


class CanonicalBot(OneTimeBot, ABC):
    def __init__(self, wiki: Site = None, debug: bool = True,
                 log_to_screen: bool = True, log_to_wiki: bool = True):
        OneTimeBot.__init__(self, wiki, debug, log_to_screen, log_to_wiki)
        self.data = PersistedData(bot_name=self.bot_name)
        self.new_data_model = datetime.min

    def __enter__(self):
        OneTimeBot.__enter__(self)
        if self.data_outdated():
            self.data.assign_dict({})
            self.logger.warning("The data is thrown away. It is out of date")
        elif (self.timestamp.last_run is None) or not self.timestamp.success_last_run:
            self.data.assign_dict({})
            self.logger.warning("The last run wasn\'t successful. The data is thrown away.")
        else:
            self.data.load()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.success:
            self.data.dump(success=True)
        else:
            self.data.dump(success=False)
            self.logger.critical("There was an error in the general procedure. "
                                 "The broken data and a backup of the old will be keept.")
        OneTimeBot.__exit__(self, exc_type, exc_val, exc_tb)

    @abstractmethod
    def task(self) -> bool:
        pass

    def create_timestamp_for_search(self, days_in_past=1) -> datetime:
        start_of_search: datetime = self.timestamp.last_run
        if self.last_run_successful:
            start_of_search = self.timestamp.last_run - timedelta(days=days_in_past)
        return start_of_search

    def data_outdated(self) -> bool:
        outdated = False
        if self.new_data_model and self.timestamp.last_run:
            if self.timestamp.last_run < self.new_data_model:
                outdated = True
                self.timestamp.last_run = None
        return outdated

    @property
    def last_run_successful(self) -> bool:
        return self.timestamp.last_run and self.timestamp.success_last_run
