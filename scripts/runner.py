__author__ = 'erik'

import sys
import os
import pywikibot
from datetime import datetime
from pywikibot.data.api import LoginManager
from scripts.service_scripts.authorlist import AuthorList

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + os.sep + os.pardir + os.sep + os.pardir + os.sep)

from tools.bots import PingBot, SaveExecution

if __name__ == "__main__":
    with open('password.pwd') as password:
        wiki = pywikibot.Site(code= 'de', fam= 'wikisource', user='THEbotIT')
        login = LoginManager(site=wiki, password=password.read())
        login.login()

    #daily bots
    bot = PingBot(wiki)
    with SaveExecution(bot):
        bot.run()

    bot = AuthorList(wiki)
    with SaveExecution(bot):
        bot.run()

    if datetime.now().weekday() == 6:
        #tasks for sunday
        pass