import sys
import os
import pywikibot
from datetime import datetime
from pywikibot.data.api import LoginManager

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + os.sep + os.pardir + os.sep)

from scripts.service_scripts.authorlist import AuthorList
from scripts.service_scripts.project_status_RE import REStatus
from tools.bots import PingBot, SaveExecution
from tools.little_helpers import load_password

def run_bot(bot):
    with SaveExecution(bot):
        bot.run()

if __name__ == "__main__":
    with open('password.pwd') as password_file:
        password = load_password(password_file)
        wiki = pywikibot.Site(code='de', fam='wikisource', user='THEbotIT')
        login = LoginManager(site=wiki, password=password)
        login.login()

    # daily bots
    run_bot(PingBot(wiki))
    run_bot(AuthorList(wiki))
    run_bot(REStatus(wiki))

    # tasks for sunday
    if datetime.now().weekday() == 6:
        pass
