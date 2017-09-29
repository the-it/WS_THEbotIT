import codecs
import logging
import sys
import os
import time
from datetime import datetime, timedelta
import json
from pywikibot import Page, Site


class BotExeption(Exception):
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
        self.debug = debug
        self.last_run = {}
        self.filename = 'data/{}.last_run.json'.format(self.bot_name)
        self.timeformat = '%Y-%m-%d_%H:%M:%S'
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

    def tear_down_timestamp(self):
        if self.success:
            if not os.path.isdir("data"):
                os.mkdir("data")
            with open(self.filename, "w") as file_pointer:
                json.dump({'success': True, 'timestamp': self.timestamp_start},
                          file_pointer,
                          default=lambda obj: obj.strftime(self.timeformat) if isinstance(obj, datetime) else obj)
            self.logger.info("Timestamp successfully kept.")
        else:
            self.logger.warning("The bot run was\'t successful. Timestamp will be kept.")
            with open(self.filename, "w") as file_pointer:
                json.dump({'success': False, 'timestamp': self.timestamp_start},
                          file_pointer,
                          default=lambda obj: obj.strftime(self.timeformat) if isinstance(obj, datetime) else obj)

    def set_up_logger(self):
        if not os.path.exists('data'):
            os.makedirs('data')
        self.logger_names.update({'debug': 'data/{}_DEBUG_{}.log'.format(self.bot_name,
                                                                         time.strftime('%y%m%d%H%M%S',
                                                                                       time.localtime()))})
        self.logger_names.update({'info': 'data/{}_INFO_{}.log'.format(self.bot_name,
                                                                       time.strftime('%y%m%d%H%M%S',
                                                                                     time.localtime()))})
        logger = logging.getLogger(self.bot_name)
        logger.setLevel(logging.DEBUG)
        error_log = logging.FileHandler(self.logger_names['info'], encoding='utf8')
        error_log.setLevel(logging.INFO)
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
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
    def __init__(self, wiki, debug):
        BaseBot.__init__(self, wiki, debug)


class CanonicalBot(BaseBot):
    def __init__(self, wiki, debug):
        BaseBot.__init__(self, wiki, debug)
        self.new_data_model = None

    def __enter__(self):
        BaseBot.__enter__(self)
        self.data_filename = 'data/{}.data.json'.format(self.bot_name)
        try:
            if self.data_outdated():
                self.data = {}
                self.logger.warning('The data is thrown away. It is out of date')
            elif (self.last_run is None) or (self.last_run['success'] == False):
                self.data = {}
                self.logger.warning('The last run wasn\'t successful. The data is thrown away.')
            else:
                with open(self.data_filename) as filepointer:
                    self.data = json.load(filepointer)
                self.logger.info("Open existing data.")
                try:
                    os.rename(self.data_filename, self.data_filename + ".deprecated")
                except OSError:
                    self.logger.error("It wasn't possible to move the data to .deprecated")
        except IOError:
            self.data = {}
            self.logger.warning("No existing data available.")
        return self

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


if __name__ == "__main__":
    wiki = Site(code='de', fam='wikisource', user='THEbotIT')
    with PingCanonical(wiki=wiki, debug=False) as bot:
        bot.run()
