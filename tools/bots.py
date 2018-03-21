from collections import Mapping
from datetime import datetime, timedelta
import json
import logging
import os
import sys

from pywikibot import Page, Site


class BotExeption(Exception):
    pass


_DATA_PATH = os.path.expanduser("~") + os.sep + ".wiki_bot"


def _get_data_path():
    if not os.path.exists(_DATA_PATH):
        os.mkdir(_DATA_PATH)
    return _DATA_PATH


class WikiLogger(object):
    _logger_format = '[%(asctime)s] [%(levelname)-8s] [%(message)s]'
    _logger_date_format = "%H:%M:%S"
    _wiki_timestamp_format = '%d.%m.%y um %H:%M:%S'

    def __init__(self, bot_name: str, start_time: datetime, silence=False):
        self._bot_name = bot_name
        self._start_time = start_time
        self._data_path = _get_data_path()
        self._logger = logging.getLogger(self._bot_name)
        self._logger_names = self._get_logger_names()
        self._silence = silence

    def __enter__(self):
        self._setup_logger_properties()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.tear_down()

    def tear_down(self):
        for handler in self._logger.handlers[:]:
            handler.close()
            self._logger.removeHandler(handler)
        if os.path.isfile(self._data_path + os.sep + self._logger_names['info']):
            os.remove(self._data_path + os.sep + self._logger_names['info'])
        sys.stdout.flush()
        logging.shutdown()

    def _get_logger_names(self):
        log_file_names = {}
        for log_type in ("info", "debug"):
            log_file_names.update({log_type: '{name}_{log_type}_{timestamp}.log'.format(
                name=self._bot_name,
                log_type=log_type.upper(),
                timestamp=self._start_time.strftime('%y%m%d%H%M%S'))})
        return log_file_names

    def _setup_logger_properties(self):
        self._logger.setLevel(logging.DEBUG)
        error_log = logging.FileHandler(self._data_path + os.sep + self._logger_names['info'],
                                        encoding='utf8')
        error_log.setLevel(logging.INFO)
        debug_log = logging.FileHandler(self._data_path + os.sep + self._logger_names['debug'],
                                        encoding='utf8')
        debug_log.setLevel(logging.DEBUG)
        formatter = logging.Formatter(self._logger_format, datefmt=self._logger_date_format)
        error_log.setFormatter(formatter)
        debug_log.setFormatter(formatter)
        self._logger.addHandler(error_log)
        self._logger.addHandler(debug_log)
        if not self._silence:
            # this activates the output of the logger
            debug_stream = logging.StreamHandler(sys.stdout)  # pragma: no cover
            debug_stream.setLevel(logging.DEBUG)  # pragma: no cover
            debug_stream.setFormatter(formatter)  # pragma: no cover
            self._logger.addHandler(debug_stream)  # pragma: no cover

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

    def create_wiki_log_lines(self):
        with open(self._data_path + os.sep + self._logger_names['info'], encoding='utf8') \
                as filepointer:
            line_list = list()
            for line in filepointer:
                line_list.append(line.strip())
            log_lines = ""
            log_lines = log_lines \
                + '\n\n' \
                + '==Log of {}=='.format(self._start_time.strftime(self._wiki_timestamp_format)) \
                + '\n\n' \
                + '\n\n'.join(line_list) \
                + '\n--~~~~'
            return log_lines


class PersistedTimestamp(object):
    _timeformat = '%Y-%m-%d_%H:%M:%S'

    def __init__(self, bot_name: str):
        self._last_run = None
        self._success_last_run = False
        self._success_this_run = False
        self._start = datetime.now()
        self._data_path = _get_data_path()
        self._full_filename = self._data_path + os.sep + "{}.last_run.json".format(bot_name)

    def __enter__(self):
        self.set_up()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.tear_down()

    def set_up(self):
        try:
            with open(self._full_filename, mode="r") as persist_json:
                last_run_dict = json.load(persist_json)
                self._last_run = datetime.strptime(last_run_dict["timestamp"], self._timeformat)
                self._success_last_run = last_run_dict["success"]
            os.remove(self._full_filename)
        except FileNotFoundError:
            self._success_last_run = False
            self._last_run = None

    def tear_down(self):
        with open(self._full_filename, mode="w") as persist_json:
            json.dump({"timestamp": self._start.strftime(self._timeformat),
                       "success": self.success_this_run},
                      persist_json)

    @property
    def last_run(self):
        return self._last_run

    @last_run.setter
    def last_run(self, value):
        if value is None:
            self._last_run = value

    @property
    def start_of_run(self):
        return self._start

    @property
    def success_last_run(self):
        return self._success_last_run

    @property
    def success_this_run(self):
        return self._success_this_run

    @success_this_run.setter
    def success_this_run(self, new_value: bool):
        if isinstance(new_value, bool):
            self._success_this_run = new_value
        else:
            raise TypeError("success_this_run is a boolean value.")


class OneTimeBot(object):
    task = None

    def __init__(self, wiki: Site = None, debug: bool = True, silence: bool = False):
        self.success = False
        self._silence = silence
        if not self.task:
            raise NotImplementedError('The class function \"task\" must be implemented!\n'
                                      'Example:\n'
                                      'class DoSomethingBot(OneTimeBot):\n'
                                      '    def task(self):\n'
                                      '        do_stuff()')
        self.timestamp = PersistedTimestamp(bot_name=self.bot_name)
        self.wiki = wiki
        self.debug = debug
        self.timeout = timedelta(days=1)
        self.logger = WikiLogger(self.bot_name, self.timestamp.start_of_run, silence=self._silence)

    def __enter__(self):
        self.timestamp.__enter__()
        self.logger.__enter__()
        self.logger.info('Start the bot {}.'.format(self.bot_name))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.timestamp.success_this_run = self.success
        self.timestamp.__exit__(exc_type, exc_val, exc_tb)
        self.logger.info('Finish bot {} in {}.'
                         .format(self.bot_name, datetime.now() - self.timestamp.start_of_run))
        if not self._silence:
            self.send_log_to_wiki()
        self.logger.__exit__(exc_type, exc_val, exc_tb)

    @classmethod
    def get_bot_name(cls):
        return cls.__name__

    @property
    def bot_name(self):
        return self.get_bot_name()

    def run(self):
        try:
            self.success = bool(self.task())  # pylint: disable=not-callable
        except Exception as catched_exception:  # pylint: disable=broad-except
            self.logger.exception("Logging an uncaught exception", exc_info=catched_exception)
            self.success = False
        return self.success

    def _watchdog(self):
        time_over = False
        if self.timeout:
            diff = datetime.now() - self.timestamp.start_of_run
            if diff > self.timeout:
                self.logger.warning('Bot finished by timeout.')
                time_over = True
        return time_over

    def send_log_to_wiki(self):
        wiki_log_page = 'Benutzer:THEbotIT/Logs/{}'.format(self.bot_name)
        page = Page(self.wiki, wiki_log_page)
        page.text += self.logger.create_wiki_log_lines()
        page.save('Update of Bot {}'.format(self.bot_name), botflag=True)


class PersistedData(Mapping):
    def __init__(self, bot_name: str):
        self.data = {}
        self.botname = bot_name
        self.data_folder = _get_data_path()
        self.file_name = self.data_folder + os.sep + bot_name + ".data.json"

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __delitem__(self, key):
        del self.data[key]

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return iter(self.data)

    def assign_dict(self, new_dict: dict):
        if isinstance(new_dict, dict):
            self.data = new_dict
        else:
            raise BotExeption("{} has the wrong type. It must be a dictionary.".format(new_dict))

    def dump(self, success=True):
        if success:
            with open(self.file_name, mode="w") as json_file:
                json.dump(self.data, json_file, indent=2)
            if os.path.isfile(self.file_name + ".deprecated"):
                os.remove(self.file_name + ".deprecated")
        else:
            with open(self.file_name + ".broken", mode="w") as json_file:
                json.dump(self.data, json_file, indent=2)

    def load(self):
        if os.path.exists(self.file_name):
            with open(self.file_name, mode="r") as json_file:
                self.data = json.load(json_file)
            os.rename(self.file_name, self.file_name + ".deprecated")
        else:
            raise BotExeption("Not data to load.")

    def update(self, dict_to_update: dict):
        self.data.update(dict_to_update)


class CanonicalBot(OneTimeBot):
    def __init__(self, wiki: Site = None, debug: bool = True, silence: bool = False):
        OneTimeBot.__init__(self, wiki, debug, silence)
        self.data = PersistedData(bot_name=self.bot_name)
        self.new_data_model = datetime.min

    def __enter__(self):
        OneTimeBot.__enter__(self)
        if self.data_outdated():
            self.data.assign_dict({})
            self.logger.warning('The data is thrown away. It is out of date')
        elif (self.timestamp.last_run is None) or not self.timestamp.success_last_run:
            self.data.assign_dict({})
            self.logger.warning('The last run wasn\'t successful. The data is thrown away.')
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

    def create_timestamp_for_search(self, days_in_past=1) -> datetime:
        if self.last_run_successful:
            start_of_search = self.timestamp.last_run - timedelta(days=days_in_past)
        else:
            start_of_search = self.timestamp.start_of_run - timedelta(days=days_in_past)
        return start_of_search

    def data_outdated(self):
        outdated = False
        if self.new_data_model and self.timestamp.last_run:
            if self.timestamp.last_run < self.new_data_model:
                outdated = True
                self.timestamp.last_run = None
        return outdated

    @property
    def last_run_successful(self) -> bool:
        return self.timestamp.last_run and self.timestamp.success_last_run
