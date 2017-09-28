from abc import ABCMeta, abstractmethod
import logging
import sys
import os
import time
from datetime import datetime, timedelta
import json
import pywikibot


class BotExeption(Exception):
    pass


class Tee(object):
    def __init__(self, *files):
        self.files = files

    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()  # If you want the output to be visible immediately

    def flush(self):
        for f in self.files:
            f.flush()


class BaseBot(object):
    __metaclass__ = ABCMeta
    bot_name = None

    def __init__(self, main_wiki, debug):
        self.timestamp_start = datetime.now()
        self.timestamp_nice = self.timestamp_start.strftime('%d.%m.%y um %H:%M:%S')
        self.wiki = main_wiki
        self.bar_string = '{:#^120}'.format('')
        self.logger_format = '[%(asctime)s] [%(levelname)-8s] [%(message)s]'
        self.logger_date_format = "%H:%M:%S"
        self.debug = debug
        self.last_run = {}
        if not self.bot_name:
            raise NotImplementedError('The class variable bot_name is not implemented. Implement the variable.')
        self.timeout = timedelta(minutes=60)

    def __enter__(self):
        self.logger_names = {}
        self.logger = self.set_up_logger()
        print(self.bar_string)
        self.logger.info('Start the bot {}.'.format(self.bot_name))
        print(self.bar_string)
        self.set_up_timestamp()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.tear_down_timestamp(exc_type)
        print(self.bar_string)
        self.logger.info('Finish bot {} in {}.'.format(self.bot_name, datetime.now() - self.timestamp_start))
        print(self.bar_string)
        self.tear_down_logger()

    def task(self):
        self.logger.critical("You should really add functionality here.")
        raise BotExeption

    def run(self):
        try:
            self.task()
        except Exception as e:
            self.logger.exception("Logging an uncaught exception", exc_info=e)
            raise BotExeption('There was a not handled Exception.')

    def _watchdog(self):
        diff = datetime.now() - self.timestamp_start
        if diff > self.timeout:
            self.logger.info('Bot finished by timeout.')
            return True
        else:
            return False

    def set_up_timestamp(self):
        self.filename = 'data/{}.last_run.json'.format(self.bot_name)
        self.timeformat = '%Y-%m-%d_%H:%M:%S'
        try:
            with open(self.filename, 'r') as filepointer:
                self.last_run = json.load(filepointer)
                self.last_run['timestamp'] = datetime.strptime(self.last_run['timestamp'], self.timeformat)
            self.logger.info("Open existing timestamp.")
            try:
                os.remove(self.filename)
            except OSError:
                pass
        except:
            self.logger.warning("it wasn't possible to retrieve an existing timestamp.")
            self.last_run = None

    def tear_down_timestamp(self, exc_type):
        if not exc_type:
            if not os.path.isdir("data"):
                os.mkdir("data")
            with open(self.filename, "w") as filepointer:
                json.dump({'succes': True, 'timestamp': self.timestamp_start}, filepointer, default=lambda obj:obj.strftime(self.timeformat) if isinstance(obj, datetime) else obj)
            self.logger.info("Timestamp successfully kept.")
        else:
            self.logger.critical("There was an error in the general procedure. Timestamp will be kept.")
            with open(self.filename, "w") as filepointer:
                json.dump({'succes': False, 'timestamp': self.timestamp_start}, filepointer, default=lambda obj:obj.strftime(self.timeformat) if isinstance(obj, datetime) else obj)

    def set_up_logger(self):
        if not os.path.exists('data'):
            os.makedirs('data')
        self.logger_names.update({'debug': 'data/{}_DEBUG_{}.log'.format(self.bot_name,
                                                                         time.strftime('%y%m%d%H%M%S', time.localtime()))})
        self.logger_names.update({'info': 'data/{}_INFO_{}.log'.format(self.bot_name,
                                                                       time.strftime('%y%m%d%H%M%S', time.localtime()))})
        # redirect the stdout to the terminal and a file
        file = open(self.logger_names['debug'], 'a', encoding='utf8')
        sys.stdout = Tee(sys.stdout, file)

        logger = logging.getLogger(self.bot_name)
        logger.setLevel(logging.DEBUG)
        error_log = logging.FileHandler(self.logger_names['info'], encoding='utf8')
        error_log.setLevel(logging.INFO)
        debug_stream = logging.StreamHandler(sys.stdout)
        debug_stream.setLevel(logging.DEBUG)
        formatter = logging.Formatter(self.logger_format, datefmt=self.logger_date_format)
        error_log.setFormatter(formatter)
        debug_stream.setFormatter(formatter)
        logger.addHandler(error_log)
        logger.addHandler(debug_stream)
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

    @abstractmethod
    def send_log_to_wiki(self):
        pass

    def dump_log_lines(self, page):
        with open(self.logger_names['info'], encoding='utf8') as filepointer:
            temptext = page.text
            temptext = temptext \
                + '\n\n' \
                + '==Log of {}=='.format(self.timestamp_nice) \
                + '\n\n' \
                + filepointer.read().replace('\n', '\n\n')
            page.text = temptext + '\n--~~~~'
            page.save('Update of Bot {}'.format(self.bot_name), botflag=True)


class OneTimeBot(BaseBot):
    def send_log_to_wiki(self):
        wiki_log_page = 'Benutzer:THEbotIT/Logs/{}'.format(self.bot_name)
        page = pywikibot.Page(self.wiki, wiki_log_page)
        self.dump_log_lines(page)


class CanonicalBot(BaseBot):
    def __init__(self, main_wiki, debug):
        BaseBot.__init__(self, main_wiki, debug)
        self.new_data_model = None

    def __enter__(self):
        BaseBot.__enter__(self)
        self.data_filename = 'data/{}.data.json'.format(self.bot_name)
        try:
            with open(self.data_filename) as filepointer:
                self.data = json.load(filepointer)
            self.logger.info("Open existing data.")
            try:
                os.rename(self.data_filename, self.data_filename + ".deprecated")
            except:
                pass
        except IOError:
            self.data = {}
            self.logger.warning("No existing data available.")
        if self.data_outdated():
            self.data = {}
            self.logger.warning('The data is thrown away. It is out of date')

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not exc_type:
            if not os.path.isdir("data"):
                os.mkdir("data")
            with open(self.data_filename, "w") as filepointer:
                json.dump(self.data, filepointer)
            if os.path.exists(self.data_filename + ".deprecated"):
                os.remove(self.data_filename + ".deprecated")
            if os.path.exists(self.data_filename + ".broken"):
                os.remove(self.data_filename + ".broken")
            self.logger.info("Data successfully stored.")
        else:
            with open(self.data_filename + '.broken', "w") as filepointer:
                json.dump(self.data, filepointer)
            self.logger.critical("There was an error in the general procedure. The broken date and a backup of the old will be keept.")
        BaseBot.__exit__(self, exc_type, exc_val, exc_tb)

    def send_log_to_wiki(self):
        wiki_log_page = 'Benutzer:THEbotIT/Logs/{}'.format(self.bot_name)
        page = pywikibot.Page(self.wiki, wiki_log_page)
        self.dump_log_lines(page)

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

    def __init__(self, main_wiki, debug):
        OneTimeBot.__init__(self, main_wiki, debug)

    def task(self):
        self.logger.info('PingOneTime')


class PingCanonical(CanonicalBot):
    bot_name = 'PingCanonical'

    def __init__(self, main_wiki, debug):
        CanonicalBot.__init__(self, main_wiki, debug)

    def task(self):
        self.logger.info('PingCanonical')
        self.logger.info('äüö')
        raise Exception('wuhahaha')


class SaveExecution:
    def __init__(self, bot: BaseBot):
        self.bot = bot

    def __enter__(self):
        self.bot.__enter__()
        return self.bot

    def __exit__(self, type, value, traceback):
        self.bot.__exit__(type, value, traceback)

if __name__ == "__main__":
    wiki = pywikibot.Site(code='de', fam='wikisource', user='THEbotIT')
    bot = PingCanonical(main_wiki=wiki, debug=False)
    with SaveExecution(bot):
        bot.run()
