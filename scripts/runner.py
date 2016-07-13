import sys
import os
import pywikibot
from datetime import datetime
from pywikibot.data.api import LoginManager
from scripts.service_scripts.authorlist import AuthorList
from scripts.service_scripts.project_status_RE import REStatus

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + os.sep + os.pardir + os.sep + os.pardir + os.sep)

from tools.bots import PingBot, SaveExecution

def run_bot(bot):
    with SaveExecution(bot):
        bot.run()

if __name__ == "__main__":
    with open('password.pwd') as password:
        wiki = pywikibot.Site(code='de', fam='wikisource', user='THEbotIT')
        login = LoginManager(site=wiki, password=password.read())
        login.login()

    # daily bots
    # run_bot(PingBot(wiki))
    run_bot(AuthorList(wiki))
    run_bot(REStatus(wiki))

    # tasks for sunday
    if datetime.now().weekday() == 6:
        pass