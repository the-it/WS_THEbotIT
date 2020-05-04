import codecs
import sys

from pywikibot import Site

from service.author_list import AuthorList
from service.gl.create_magazine import GlCreateMagazine
from service.gl.status import GlStatus
from service.ws_re.register.printer import ReRegisterPrinter
from service.ws_re.scanner.base import ReScanner
from service.ws_re.status import ReStatus
from tools.bot_scheduler import BotScheduler

if __name__ == "__main__":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())  # type: ignore
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    SCHEDULER = BotScheduler(wiki=WS_WIKI, debug=False)
    SCHEDULER.daily_bots = [AuthorList, ReScanner, ReRegisterPrinter]
    SCHEDULER.weekly_bots = {0: [],  # monday
                             1: [],
                             2: [],
                             3: [],
                             4: [],
                             5: [],
                             6: [ReStatus, GlCreateMagazine]}  # sunday
    SCHEDULER.monthly_bots = {1: [GlStatus]}
    SCHEDULER.bots_on_last_day_of_month = []
    with SCHEDULER as bot:
        bot.run()
