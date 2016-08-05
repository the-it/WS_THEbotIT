import sys
import datetime

from pywikibot import Page
from tools.bots import CanonicalBot

class PingBot(CanonicalBot):
    def __init__(self, wiki, debug):
        CanonicalBot.__init__(self, wiki, debug)
        self.botname = 'PingBot'

    def run(self):
        self.logger.info(sys.path)
        lemma = Page(self.wiki, 'Benutzer:THEbotIT/{}'.format(self.botname))
        lemma.text = "The current time is {} \npath: {}".format(datetime.datetime.now().strftime('%S'), sys.path)
        lemma.save('save the page', botflag=True)