from datetime import date, datetime

from pywikibot import Site

from service.ws_re.register.statistic.base import PAST_YEARS, STATISTIC_VOLUMES
from service.ws_re.register.statistic.chart import HistoryCharts
from service.ws_re.register.statistic.picture import ProofReadPicture
from tools.bots.cloud_bot import CloudBot


class ReStatistic(CloudBot):
    def task(self) -> bool:
        assert self.wiki is not None
        today = datetime.now().date()
        # the picture of a past year shows the state at its end, the one of the current year the state of today.
        # An unchanged picture isn't uploaded again.
        for year in PAST_YEARS:
            if year < today.year:
                ProofReadPicture(self.wiki, self.logger, date(year, 12, 31)).update()
        ProofReadPicture(self.wiki, self.logger, today).update()
        for volume_name in STATISTIC_VOLUMES:
            ProofReadPicture(self.wiki, self.logger, today).update_volume(volume_name)
        self.update_history_chart(today)
        return True

    def update_history_chart(self, today: date) -> None:
        assert self.wiki is not None
        commons = Site(code="commons", fam="commons", user="THEbotIT")
        HistoryCharts(self.wiki, commons, self.logger).update(today)


if __name__ == "__main__":  # pragma: no cover
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    with ReStatistic(wiki=WS_WIKI, debug=True, log_to_wiki=False) as bot:
        bot.run()
