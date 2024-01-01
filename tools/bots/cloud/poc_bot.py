from datetime import datetime, UTC
import time
import random

from pywikibot import Site

from tools.bots.cloud.cloud_bot import CloudBot


class Poc(CloudBot):
    def task(self) -> bool:
        self.data["time"] = datetime.now(UTC).isoformat()
        time.sleep(2)
        if random.random() > 0.5:
            raise RuntimeError("Something went wrong by chance ;-)")
        return random.choice([True, False])


if __name__ == "__main__":
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    with Poc(wiki=WS_WIKI, debug=False) as bot:
        bot.run()
