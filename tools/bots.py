import logging
import sys
import os
import time
import abc

class Tee(object):
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush() # If you want the output to be visible immediately
    def flush(self) :
        for f in self.files:
            f.flush()

class BaseBot:
    def enter(self):
        self.logger_names = {}
        self.logger = self.set_up_logger()
        self.logger.info('Start the bot {}'.format(os.path.basename(__file__)))

    def exit(self):
        self.tear_down_logger()

    def set_up_logger(self):
        if not os.path.exists('logs'):
            os.makedirs('logs')
        self.logger_names.update({'debug': 'logs/{}_DEBUG_{}.log'.format(os.path.basename(__file__), time.strftime('%y%m%d_%H%M%S', time.localtime()))})
        self.logger_names.update({'info': 'logs/{}_INFO_{}.log'.format(os.path.basename(__file__), time.strftime('%y%m%d_%H%M%S', time.localtime()))})
        #redirect the stdout to the terminal and a file
        file = open(self.logger_names['debug'], 'w')
        sys.stdout = Tee(sys.stdout, file)

        logger = logging.getLogger('multi logger')
        logger.setLevel(logging.DEBUG)
        error_log = logging.FileHandler(self.logger_names['info'])
        error_log.setLevel(logging.INFO)
        debug_stream = logging.StreamHandler(sys.stdout)
        debug_stream.setLevel(logging.DEBUG)
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)-8s] [%(message)s]')
        error_log.setFormatter(formatter)
        debug_stream.setFormatter(formatter)
        logger.addHandler(error_log)
        logger.addHandler(debug_stream)
        return logger

    def tear_down_logger(self):
        for handler in self.logger.handlers:
            handler.close()

        #todo: sent it via email
        if os.path.isfile(self.logger_names['info']):
            os.remove(self.logger_names['info'])
        sys.stdout.flush()

    def run(self):
        pass

class OneTimeBot(BaseBot):
    pass

class CanonicalBot(BaseBot):
    pass

class SaveExecution():
    def __init__(self, bot: BaseBot):
        self.bot = bot

    def __enter__(self):
        self.bot.enter()
        return self.bot

    def __exit__(self, type, value, traceback):
        self.bot.exit()

if __name__ == "__main__":
    bot = OneTimeBot()
    with SaveExecution(bot):
        bot.run()

