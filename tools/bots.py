from collections import Mapping
from datetime import datetime, timedelta
import json
import logging
import os
import sys
import time

from pywikibot import Page


class BotExeption(Exception):
    pass


def get_data_path():
    data_path = os.getcwd() + os.sep + "data"
    if not os.path.exists(data_path):
        os.mkdir(data_path)
    return data_path


class WikiLogger(object):
    def __init__(self):
        pass


class BaseBot(object):
    bot_name = None

    def __init__(self, wiki, debug):
        self.success = False
        self.timestamp_start = datetime.now()
        self.timestamp_nice = self.timestamp_start.strftime('%d.%m.%y um %H:%M:%S')
        self.wiki = wiki
        self.bar_string = '{:#^120}'.format('')
        self.logger_format = '[%(asctime)s] [%(levelname)-8s] [%(message)s]'
        self.logger_date_format = "%H:%M:%S"
        self.logger_names = {}
        self.debug = debug
        self.last_run = {}
        self.filename_timestamp = 'data/{}.last_run.json'.format(self.bot_name)
        self.timeformat = '%Y-%m-%d_%H:%M:%S'
        if not self.bot_name:
            raise NotImplementedError('The class variable bot_name is not implemented. Implement the variable.')
        self.timeout = timedelta(minutes=60)

    def __enter__(self):
        self.logger = self.set_up_logger()
        print(self.bar_string)
        self.logger.info('Start the bot {}.'.format(self.bot_name))
        print(self.bar_string)
        self.set_up_timestamp()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.tear_down_timestamp()
        print(self.bar_string)
        self.logger.info('Finish bot {} in {}.'.format(self.bot_name, datetime.now() - self.timestamp_start))
        print(self.bar_string)
        self.tear_down_logger()

    def task(self):
        self.logger.critical("You should really add functionality here.")
        raise BotExeption

    def run(self):
        try:
            self.success = bool(self.task())
        except Exception as e:
            self.logger.exception("Logging an uncaught exception", exc_info=e)
            self.success = False
        return self.success

    def _watchdog(self):
        diff = datetime.now() - self.timestamp_start
        if diff > self.timeout:
            self.logger.warning('Bot finished by timeout.')
            return True
        else:
            return False

    def set_up_timestamp(self):
        try:
            with open(self.filename_timestamp, 'r') as filepointer:
                self.last_run = json.load(filepointer)
                self.last_run['timestamp'] = datetime.strptime(self.last_run['timestamp'], self.timeformat)
            self.logger.info("Open existing timestamp.")
            try:
                os.remove(self.filename_timestamp)
            except OSError:
                pass
        except:
            self.logger.warning("it wasn't possible to retrieve an existing timestamp.")
            self.last_run = None

    def _dumb_timestamp(self, success: bool):
        with open(self.filename_timestamp, "w") as file_pointer:
            json.dump({'success': success, 'timestamp': self.timestamp_start},
                      file_pointer,
                      default=lambda obj: obj.strftime(self.timeformat) if isinstance(obj, datetime) else obj)

    def tear_down_timestamp(self):
        if self.success:
            if not os.path.isdir("data"):
                os.mkdir("data")
            self._dumb_timestamp(True)
            self.logger.info("Timestamp successfully kept.")
        else:
            self._dumb_timestamp(False)
            self.logger.warning("The bot run was\'t successful. Timestamp will be kept.")

    def _update_logger_name(self, log_type: str):
        self.logger_names.update({log_type: 'data/{name}_{log_type}_{timestamp}.log'
                                               .format(name = self.bot_name,
                                                       log_type = log_type.capitalize(),
                                                       timestamp = time.strftime('%y%m%d%H%M%S', time.localtime()))})

    def set_up_logger(self):
        if not os.path.exists('data'):
            os.makedirs('data')
        self._update_logger_name("debug")
        self._update_logger_name("info")
        logger = logging.getLogger(self.bot_name)
        logger.setLevel(logging.DEBUG)
        error_log = logging.FileHandler(self.logger_names['info'], encoding='utf8')
        error_log.setLevel(logging.INFO)
        debug_stream = logging.StreamHandler(sys.stdout)
        debug_stream.setLevel(logging.DEBUG)
        debug_log = logging.FileHandler(self.logger_names['debug'], encoding='utf8')
        debug_log.setLevel(logging.DEBUG)
        formatter = logging.Formatter(self.logger_format, datefmt=self.logger_date_format)
        error_log.setFormatter(formatter)
        debug_stream.setFormatter(formatter)
        debug_log.setFormatter(formatter)
        logger.addHandler(error_log)
        logger.addHandler(debug_stream)
        logger.addHandler(debug_log)
        return logger

    def tear_down_logger(self):
        for handler in self.logger.handlers:
            handler.close()
        if not self.debug:
            self.send_log_to_wiki()
        if os.path.isfile(self.logger_names['info']):
            os.remove(self.logger_names['info'])
            pass
        sys.stdout.flush()
        logging.shutdown()

    def send_log_to_wiki(self):
        wiki_log_page = 'Benutzer:THEbotIT/Logs/{}'.format(self.bot_name)
        page = Page(self.wiki, wiki_log_page)
        self.dump_log_lines(page)

    def dump_log_lines(self, page):
        with open(self.logger_names['info'], encoding='utf8') as filepointer:
            line_list = list()
            for line in filepointer:
                line_list.append(line.strip())
            temptext = page.text
            temptext = temptext \
                + '\n\n' \
                + '==Log of {}=='.format(self.timestamp_nice) \
                + '\n\n' \
                + '\n\n'.join(line_list)
            page.text = temptext + '\n--~~~~'
            page.save('Update of Bot {}'.format(self.bot_name), botflag=True)


class OneTimeBot(BaseBot):
    pass


class PersistedData(Mapping):
    def __init__(self, bot_name: str):
        self.data = {}
        self.botname = bot_name
        self.data_folder = _data_folder
        self.file_name = self.data_folder + os.sep + bot_name + ".data.json"

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return iter(self.data)

    def assign_dict(self, new_dict: dict):
        if type(new_dict) is dict:
            self.data = new_dict
        else:
            raise BotExeption("{} has the wrong type. It must be a dictionary.".format(new_dict))

    def dump(self, success=True):
        if not os.path.exists(self.data_folder):
            os.mkdir(self.data_folder)
        if success:
            with open(self.file_name, mode="w") as json_file:
                json.dump(self.data, json_file)
            if os.path.isfile(self.file_name + ".deprecated"):
                os.remove(self.file_name + ".deprecated")
        else:
            with open(self.file_name + ".broken", mode="w") as json_file:
                json.dump(self.data, json_file)

    def load(self):
        if os.path.exists(self.file_name):
            with open(self.file_name, mode="r") as json_file:
                self.data = json.load(json_file)
            os.rename(self.file_name, self.file_name + ".deprecated")
        else:
            raise BotExeption("Not data to load.")


class CanonicalBot(BaseBot):
    def __init__(self, wiki, debug):
        BaseBot.__init__(self, wiki, debug)
        self.data = PersistedData(bot_name=self.bot_name)
        self.new_data_model = None

    def __enter__(self):
        BaseBot.__enter__(self)
        if self.data_outdated():
            self.data.assign_dict({})
            self.logger.warning('The data is thrown away. It is out of date')
        elif (self.last_run is None) or (self.last_run['success'] == False):
            self.data.assign_dict({})
            self.logger.warning('The last run wasn\'t successful. The data is thrown away.')
        else:
            self.data.load()
        return self

    @staticmethod
    def _remove_file_if_exists(file_name):
        if os.path.exists(file_name):
            os.remove(file_name)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not exc_type:
            self.data.dump(success=True)
        else:
            self.data.dump(success=False)
            self.logger.critical("There was an error in the general procedure. "
                                 "The broken data and a backup of the old will be keept.")
        BaseBot.__exit__(self, exc_type, exc_val, exc_tb)

    def create_timestamp_for_search(self, searcher, days_in_past=1):
        if self.last_run:
            start_of_search = self.last_run['timestamp'] - timedelta(days=days_in_past)
        else:
            start_of_search = self.timestamp_start - timedelta(days=days_in_past)
        searcher.last_change_after(int(start_of_search.strftime('%Y')),
                                   int(start_of_search.strftime('%m')),
                                   int(start_of_search.strftime('%d')))
        self.logger.info('The date {} is set to the argument "after".'
                         .format(start_of_search.strftime("%d.%m.%Y")))

    def data_outdated(self):
        outdated = False
        if self.new_data_model and self.last_run:
            if self.last_run['timestamp'] < self.new_data_model:
                outdated = True
                self.last_run = None
        return outdated


class PingOneTime(OneTimeBot):
    bot_name = 'PingOneTime'

    def __init__(self, wiki, debug):
        OneTimeBot.__init__(self, wiki, debug)

    def task(self):
        self.logger.info('PingOneTime')
        return True


class PingCanonical(CanonicalBot):
    bot_name = 'PingCanonical'

    def task(self):
        self.logger.info('PingCanonical')
        self.logger.debug('äüö')
        return True
