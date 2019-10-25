import codecs
import sys

from pywikibot import Site

from scripts.service.author_list import AuthorList
from scripts.service.gl.create_magazine import GlCreateMagazine
from scripts.service.gl.status import GlStatus
from scripts.service.ws_re.register.printer import ReRegisterPrinter
from scripts.service.ws_re.scanner import ReScanner
from scripts.service.ws_re.status import ReStatus
from tools.bot_scheduler import BotScheduler

if __name__ == "__main__":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())  # type: ignore
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    SCHEDULER = BotScheduler(wiki=WS_WIKI, debug=False)
    SCHEDULER.daily_bots = (AuthorList)
    SCHEDULER.weekly_bots = {0: [ReScanner],  # monday
                             1: [],
                             2: [],
                             3: [],
                             4: [ReScanner],
                             5: [],
                             6: (ReStatus, GlCreateMagazine, ReRegisterPrinter)}  # sunday
    SCHEDULER.monthly_bots = {1: (GlStatus,)}
    SCHEDULER.bots_on_last_day_of_month = []
    with SCHEDULER as bot:
        bot.run()
