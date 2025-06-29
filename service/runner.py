import codecs
import sys

from pywikibot import Site

from service.finisher import Finisher
from service.list_bots.author_list import AuthorList
from service.gl.status import GlStatus
from service.list_bots.poem_list import PoemList
from service.ws_re.register.printer import ReRegisterPrinter
from service.ws_re.scanner.base import ReScanner
from tools.bot_scheduler import BotScheduler

if __name__ == "__main__":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())  # type: ignore
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    SCHEDULER = BotScheduler(wiki=WS_WIKI, debug=False)
    SCHEDULER.daily_bots = [AuthorList, PoemList, ReScanner, ReRegisterPrinter, Finisher]
    SCHEDULER.weekly_bots = {
        0: [],  # monday
        1: [],
        2: [],
        3: [],
        4: [],
        5: [],
        6: []  # sunday
    }
    SCHEDULER.monthly_bots = {1: [GlStatus]}
    SCHEDULER.bots_on_last_day_of_month = []
    with SCHEDULER as bot:
        bot.run()
