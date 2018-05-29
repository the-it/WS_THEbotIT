# -*- coding: utf-8 -*-
from pywikibot import Site

from tools.bots import OneTimeBot


class TestBot3(OneTimeBot):
    def task(self):
        return True


class TestBot4(OneTimeBot):
    def task(self):
        return True


if __name__ == "__main__":
    wiki = Site(code='de', fam='wikisource', user='THEbotIT')
    with TestBot3(wiki=wiki, debug=True) as bot:
        bot.run()
