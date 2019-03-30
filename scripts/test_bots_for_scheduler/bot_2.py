from pywikibot import Site

from tools.bots import OneTimeBot


class TestBot2(OneTimeBot):
    def task(self):
        self.logger.info(self.bot_name)
        return True


if __name__ == "__main__":
    WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    with TestBot2(wiki=WIKI, debug=True) as bot:
        bot.run()
