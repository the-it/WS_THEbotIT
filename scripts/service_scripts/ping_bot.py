import sys
import os
import re
import traceback
import datetime
from datetime import timedelta


sys.path.append(os.path.dirname(os.path.realpath(__file__)) + os.sep + os.pardir + os.sep + os.pardir + os.sep )

from pywikibot import ItemPage, Page, Site
from pywikibot.data.api import LoginManager
from tools.bots import CanonicalBot, SaveExecution
from tools.little_helpers import load_password



class PingBot(CanonicalBot):
    def __init__(self, wiki, debug):
        CanonicalBot.__init__(self, wiki, debug)
        self.botname = 'PingBot'

    def run(self):
        self.logger.info(sys.path)
        lemma = Page(self.wiki, 'Benutzer:THEbotIT/{}'.format(self.botname))
        lemma.text = "The current time is {} \npath: {}".format(datetime.datetime.now().strftime('%S'), sys.path)
        lemma.save('save the page', botflag=True)


if __name__ == "__main__":
    wiki = Site(code= 'de', fam= 'wikisource', user='THEbotIT')
    bot = PingBot(wiki=wiki, debug=True)
    with SaveExecution(bot):
        bot.run()
