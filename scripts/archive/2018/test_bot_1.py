# successful processed on 2018-06-03
# -*- coding: utf-8 -*-
from pywikibot import Site

from tools.bots import OneTimeBot


class TestBot1(OneTimeBot):
    def task(self):
        return True


if __name__ == "__main__":
    wiki = Site(code='de', fam='wikisource', user='THEbotIT')
    with TestBot1(wiki=wiki, debug=True) as bot:
        bot.run()
