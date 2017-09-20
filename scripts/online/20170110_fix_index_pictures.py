# -*- coding: utf-8 -*-
__author__ = 'eso'
import sys
import re
sys.path.append('../../')

from pywikibot import Site
from pywikibot import Page
from tools.bots import OneTimeBot, SaveExecution
from tools.catscan import PetScan

regex_picture = re.compile('\|BILD=\[\[(.*?)\]\]')


class PingOne(OneTimeBot):
    def __init__(self, wiki, debug):
        OneTimeBot.__init__(self, wiki, debug)
        self.bot_name = '20170730_Ping_One'
        self.searcher = PetScan()

    def _search(self):
        self.searcher.add_positive_category('Index')
        return self.searcher.run()

    def run(self):
        lemma_list = self._search()
        for lemma in lemma_list:
            page = Page(self.wiki, title='Index:{}'.format(lemma['title']))
            self.logger.info(page)
            match = regex_picture.search(page.text)
            if match:
                self.logger.info(match.group(1))
                if re.search('thumb', match.group(1)):
                    self.logger.info('nothing to do here')
                    break
                temp = '[[{}|thumb]]'.format(re.sub('\|\d{2,3}px', '', match.group(1)))
                self.logger.info(temp)
                temp_text = regex_picture.sub(temp, page.text)
                page.text = temp_text
                #page.save(botflag=True, summary='set thumb as parameter')


if __name__ == "__main__":
    wiki = Site(code='de', fam='wikisource', user='THEbotIT')
    bot = PingOne(wiki=wiki, debug=True)
    with SaveExecution(bot):
        bot.run()
