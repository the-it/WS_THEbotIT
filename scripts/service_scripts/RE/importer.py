import sys
import os
import pywikibot
import re
import traceback
import datetime
from datetime import timedelta
from pywikibot.data.api import LoginManager

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + os.sep + os.pardir + os.sep + os.pardir + os.sep )

from tools.catscan import CatScan
from tools.date_conversion import DateConversion
from tools.template_handler import TemplateHandler
from tools.bots import OneTimeBot, SaveExecution


class REImporter(OneTimeBot):
    def __init__(self, wiki):
        OneTimeBot.__init__(self, wiki)
        self.botname = 'REImporter'

    def run(self):
        pass


if __name__ == "__main__":
    with open('../../password.pwd') as password:
        wiki = pywikibot.Site(code= 'de', fam= 'wikisource', user='THEbotIT')
        login = LoginManager(site=wiki, password=password.read())
        login.login()

    bot = REImporter(wiki)
    with SaveExecution(bot):
        bot.run()
