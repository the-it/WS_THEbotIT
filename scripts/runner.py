import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + os.sep + os.pardir + os.sep)

from pywikibot import Site
from pywikibot.data.api import LoginManager
from scripts.service_scripts.authorlist import AuthorList
from scripts.service_scripts.project_status_RE import REStatus
from scripts.service_scripts.project_status_GL import GLStatus
from scripts.service_scripts.touch_all_index import TouchIndex
from tools.bots import SaveExecution
from tools.little_helpers import load_password

def run_bot(bot):
    with SaveExecution(bot):
        bot.run()

if __name__ == "__main__":
    with open('password.pwd') as password_file:
        wiki = Site(code='de', fam='wikisource', user='THEbotIT')
        login = LoginManager(site=wiki, password=load_password(password_file))
        login.login()

    # daily bots
    run_bot(AuthorList(wiki=wiki, debug=False))
    #run_bot(TouchIndex(wiki)) #pause because of bug fixing

    # tasks for sunday
    if datetime.now().weekday() == 6:
        run_bot(REStatus(wiki=wiki, debug=False))

    # tasks for the first day of the month
    if datetime.now().day == 1:
        run_bot(GLStatus(wiki=wiki, debug=False))
