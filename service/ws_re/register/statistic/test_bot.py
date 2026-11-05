from unittest import mock

from testfixtures import compare

from service.ws_re.register.statistic import ReStatistic


class TestReStatistic:
    def test_task_updates_picture_and_chart(self):
        bot = mock.MagicMock()
        with (
            mock.patch("service.ws_re.register.statistic.bot.ProofReadPicture") as picture_mock,
            mock.patch("service.ws_re.register.statistic.bot.HistoryCharts") as chart_mock,
            mock.patch("service.ws_re.register.statistic.bot.Site") as site_mock,
        ):
            compare(True, ReStatistic.task(bot))
            ReStatistic.update_history_chart(bot)
        picture_mock.assert_called_once_with(bot.wiki, bot.logger)
        picture_mock.return_value.update.assert_called_once_with()
        chart_mock.assert_called_once_with(bot.wiki, site_mock.return_value, bot.logger)
        site_mock.assert_called_once_with(code="commons", fam="commons", user="THEbotIT")
        compare(True, chart_mock.return_value.update.called)
