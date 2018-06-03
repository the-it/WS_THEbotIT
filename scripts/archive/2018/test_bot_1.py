# successful processed on 2018-06-03
from pywikibot import Site

from tools.bots import OneTimeBot


class TestBot1(OneTimeBot):
    def task(self):  # pragma: no cover
        self.logger.info(self.bot_name)
        return True


if __name__ == "__main__":  # pragma: no cover
    WIKI = Site(code='de', fam='wikisource', user='THEbotIT')
    with TestBot1(wiki=WIKI, debug=True) as bot:
        bot.run()
