from datetime import datetime

from pywikibot import Site

from service.ws_re.register.statistic.chart import HistoryCharts
from service.ws_re.register.statistic.picture import ProofReadPicture
from tools.bots.cloud_bot import CloudBot


class ReStatistic(CloudBot):
    def task(self) -> bool:
        assert self.wiki is not None
        ProofReadPicture(self.wiki, self.logger).update()
        self.update_history_chart()
        return True

    def update_history_chart(self) -> None:
        assert self.wiki is not None
        commons = Site(code="commons", fam="commons", user="THEbotIT")
        HistoryCharts(self.wiki, commons, self.logger).update(datetime.now().date())


if __name__ == "__main__":  # pragma: no cover
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    with ReStatistic(wiki=WS_WIKI, debug=True, log_to_wiki=False) as bot:
        bot.run()
