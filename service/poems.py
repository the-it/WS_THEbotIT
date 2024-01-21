from pywikibot import Site

from tools.bots.cloud.cloud_bot import CloudBot


class PoemBot(CloudBot):
    def task(self) -> bool:
        pass


if __name__ == "__main__":
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    with PoemBot(wiki=WS_WIKI, debug=False) as bot:
        bot.run()
