from datetime import date
from unittest import mock

from testfixtures import compare

from service.ws_re.register.statistic import ReStatistic


class TestReStatistic:
    def test_task_updates_picture_and_chart(self):
        bot = mock.MagicMock()
        with (
            mock.patch("service.ws_re.register.statistic.bot.ProofReadPicture") as picture_mock,
            mock.patch("service.ws_re.register.statistic.bot.datetime") as datetime_mock,
            mock.patch("service.ws_re.register.statistic.bot.STATISTIC_VOLUMES", ("I,1", "S III")),
        ):
            datetime_mock.now.return_value.date.return_value = date(2025, 11, 7)
            compare(True, ReStatistic.task(bot))
        # a picture of the end of the configured past years (2025 isn't past yet), the picture of the current year and
        # the charts show the same day
        compare(
            [
                mock.call(bot.wiki, bot.logger, date(2007, 12, 31)),
                mock.call(bot.wiki, bot.logger, date(2020, 12, 31)),
                mock.call(bot.wiki, bot.logger, date(2025, 11, 7)),
                # the pictures of the volumes show the state of today
                mock.call(bot.wiki, bot.logger, date(2025, 11, 7)),
                mock.call(bot.wiki, bot.logger, date(2025, 11, 7)),
            ],
            picture_mock.call_args_list,
        )
        compare(3, picture_mock.return_value.update.call_count)
        compare([mock.call("I,1"), mock.call("S III")], picture_mock.return_value.update_volume.call_args_list)
        bot.update_history_chart.assert_called_once_with(date(2025, 11, 7))

    def test_update_history_chart(self):
        bot = mock.MagicMock()
        with (
            mock.patch("service.ws_re.register.statistic.bot.HistoryCharts") as chart_mock,
            mock.patch("service.ws_re.register.statistic.bot.Site") as site_mock,
        ):
            ReStatistic.update_history_chart(bot, date(2026, 11, 7))
        site_mock.assert_called_once_with(code="commons", fam="commons", user="THEbotIT")
        chart_mock.assert_called_once_with(bot.wiki, site_mock.return_value, bot.logger)
        chart_mock.return_value.update.assert_called_once_with(date(2026, 11, 7))
