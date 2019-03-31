import codecs
import sys

from pywikibot import Site

from scripts.service.ws_re.register_printer import ReRegisterPrinter
from tools.bot_scheduler import BotScheduler

if __name__ == "__main__":  # pragma: no cover
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    SCHEDULER = BotScheduler(wiki=WS_WIKI, debug=False)
    SCHEDULER.daily_bots = [ReRegisterPrinter]
    SCHEDULER.bots_on_last_day_of_month = []
    with SCHEDULER as bot:
        bot.run()
