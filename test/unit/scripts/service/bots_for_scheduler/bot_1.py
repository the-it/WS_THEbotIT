from pywikibot import Site

from tools.bots import OneTimeBot


class TestBot1(OneTimeBot):
    def task(self):
        return True


if __name__ == "__main__":
    WIKI = Site(code='de', fam='wikisource', user='THEbotIT')
    with TestBot1(wiki=WIKI, debug=True) as bot:
        bot.run()
