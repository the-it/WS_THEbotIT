import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + os.sep + os.pardir + os.sep)

from pywikibot import Site
from scripts.service_scripts.authorlist import AuthorList
from scripts.service_scripts.project_status_RE import REStatus
from scripts.service_scripts.project_status_GL import GLStatus
from scripts.service_scripts.touch_all_index import TouchIndex
from scripts.service_scripts.create_magazine_GL import MagazinesGL
from tools.bots import SaveExecution

def run_bot(bot):
    with SaveExecution(bot):
        bot.run()

if __name__ == "__main__":
    wiki = Site(code='de', fam='wikisource', user='THEbotIT')

    # daily bots
    run_bot(AuthorList(wiki=wiki, debug=False))
    #run_bot(TouchIndex(wiki)) #pause because of bug fixing

    # tasks for monday
    if datetime.now().weekday() == 0:
        run_bot(MagazinesGL(wiki=wiki, debug=False))

    # tasks for sunday
    if datetime.now().weekday() == 6:
        run_bot(REStatus(wiki=wiki, debug=False))

    # tasks for the first day of the month
    if datetime.now().day == 1:
        run_bot(GLStatus(wiki=wiki, debug=False))
