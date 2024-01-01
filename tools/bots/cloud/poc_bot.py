from datetime import datetime, UTC
import time

from pywikibot import Site

from tools.bots.cloud.lambda_bot import LambdaBot


class Poc(LambdaBot):
    def task(self) -> bool:
        self.data["time"] = datetime.now(UTC).isoformat()
        time.sleep(5)
        self.status.current_run.output = {"blug": "something"}
        return False


if __name__ == "__main__":
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    with Poc(wiki=WS_WIKI, debug=False) as bot:
        bot.run()
