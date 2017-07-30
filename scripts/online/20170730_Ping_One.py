# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
sys.path.append('../../')

import pywikibot

from tools.bots import OneTimeBot, SaveExecution


class PingOne(OneTimeBot):
    def __init__(self, wiki, debug):
        OneTimeBot.__init__(self, wiki, debug)
        self.bot_name = '20170730_Ping_One'

    def run(self):
        self.logger.info('20170730_Ping_One')


if __name__ == "__main__":
    wiki = pywikibot.Site(code='de', fam='wikisource', user='THEbotIT')
    bot = PingOne(wiki=wiki, debug=True)
    with SaveExecution(bot):
        bot.run()
