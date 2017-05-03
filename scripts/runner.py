import calendar
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + os.sep + os.pardir + os.sep)

from pywikibot import Site
from scripts.service.author_list import AuthorList
from scripts.service.re.status import ReStatus
from scripts.service.gl.status import GlStatus
from scripts.service.gl.create_magazine import GlCreateMagazine
from scripts.service.re.scanner import ReScanner
from tools.bots import SaveExecution

def run_bot(bot):
    with SaveExecution(bot):
        bot.run()

if __name__ == "__main__":
    wiki = Site(code='de', fam='wikisource', user='THEbotIT')

    daily_list = [AuthorList, ReScanner]

    weekly_list = {0:[],#monday
                   1:[],
                   2:[],
                   3:[],
                   4:[],
                   5:[GlCreateMagazine],
                   6:[ReStatus]}#sunday

    monthly_list = {1:[GlStatus]}

    last_day_of_month = []

    #daily tasks
    for bot in daily_list:
        run_bot(bot(wiki=wiki, debug=False))

    now = datetime.now()

    # weekly tasks
    for bot in weekly_list[now.weekday()]:
        run_bot(bot(wiki=wiki, debug=False))

    # monthly tasks
    try:
        for bot in monthly_list[now.day]:
            run_bot(bot(wiki=wiki, debug=False))
    except KeyError:
        pass

    # last day of the month
    if now.day == calendar.monthrange(now.year, now.month)[1]:
        for bot in last_day_of_month:
            run_bot(bot(wiki=wiki, debug=False))
