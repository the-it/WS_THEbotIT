from datetime import datetime
from unittest import TestCase, mock

from testfixtures import LogCapture, compare

from tools.bot_scheduler import BotScheduler
from tools.bots import CanonicalBot, BotException, PersistedTimestamp


class TestBotScheduler(TestCase):
    def setUp(self):
        self.addCleanup(mock.patch.stopall)
        self.now_patcher = mock.patch("tools.bot_scheduler.BotScheduler.now", new_callable=mock.Mock())
        self.now_mock = self.now_patcher.start()
        site_mock = mock.Mock()
        site_mock.username = mock.Mock(return_value="THEbotIT")
        self.bot_scheduler = BotScheduler(site_mock, True)

    def test_get_weekday(self):
        expectation = (4, 5, 6, 0, 1, 2, 3, 4)
        for i in range(1,9):
            self.now_mock.return_value = datetime(year=2010, month=1, day=i)
            compare(expectation[i - 1] , self.bot_scheduler.now().weekday())

    def test_last_day_of_month(self):
        dates = (datetime(year=2010, month=1, day=31),
                 datetime(year=2010, month=2, day=28),
                 datetime(year=2010, month=3, day=31),
                 datetime(year=2010, month=7, day=31),
                 datetime(year=2010, month=8, day=31),
                 datetime(year=2010, month=9, day=30),
                 datetime(year=2010, month=12, day=31))
        for date in dates:
            self.now_mock.return_value = date
            self.assertTrue(self.bot_scheduler._last_day_of_month())

        dates = (datetime(year=2010, month=1, day=30),
                 datetime(year=2010, month=2, day=27),
                 datetime(year=2010, month=3, day=1),
                 datetime(year=2010, month=7, day=26),
                 datetime(year=2010, month=8, day=19))
        for date in dates:
            self.now_mock.return_value = date
            self.assertFalse(self.bot_scheduler._last_day_of_month())

    def test_bot_run(self):
        bot_mock = mock.MagicMock(spec=CanonicalBot)
        bot_mock.run.return_value = True
        bot_mock.timestamp = PersistedTimestamp("")
        with LogCapture():
            self.assertTrue(self.bot_scheduler.run_bot(bot_mock))
            compare(1, bot_mock.__enter__.call_count)
            compare(1, bot_mock.run.call_count)
            compare(1, bot_mock.__exit__.call_count)

        bot_mock.run.return_value = False
        with LogCapture():
            self.assertFalse(self.bot_scheduler.run_bot(bot_mock))

    def test_wrong_type_runner(self):
        bot = list()
        with self.assertRaises(BotException):
            self.bot_scheduler.run_bot(bot)

    class Bot1(CanonicalBot):
        def task(self):
            pass

    class Bot2(CanonicalBot):
        def task(self):
            pass

    def test_run_daily(self):
        self.bot_scheduler.daily_bots = [self.Bot1, self.Bot2]
        with mock.patch.object(self.bot_scheduler, "run_bot", mock.Mock()) as run_mock:
            self.bot_scheduler.run_dailys()
            compare(2, run_mock.call_count)
            self.assertTrue(isinstance(run_mock.mock_calls[0][1][0], self.Bot1))
            self.assertTrue(isinstance(run_mock.mock_calls[1][1][0], self.Bot2))

    def test_run_weekly(self):
        self.bot_scheduler.weekly_bots = {0: [self.Bot1], 1: [self.Bot2]}
        self.now_mock.return_value = datetime(year=2010, month=1, day=4)  # monday
        with mock.patch.object(self.bot_scheduler, "run_bot", mock.Mock()) as run_mock:
            self.bot_scheduler.run_weeklys()
            compare(1, run_mock.call_count)
            self.assertTrue(isinstance(run_mock.mock_calls[0][1][0], self.Bot1))

    def test_run_weekly_nothing_to_do(self):
        self.bot_scheduler.weekly_bots = {0: [self.Bot1], 1: [self.Bot2]}
        self.now_mock.return_value = datetime(year=2010, month=1, day=6)  # wednesday
        with mock.patch.object(self.bot_scheduler, "run_bot", mock.Mock()) as run_mock:
            self.bot_scheduler.run_weeklys()
            compare(0, run_mock.call_count)

    def test_run_monthly(self):
        self.bot_scheduler.monthly_bots = {1: [self.Bot1], 2: [self.Bot2]}
        self.now_mock.return_value = datetime(year=2010, month=1, day=2)
        with mock.patch.object(self.bot_scheduler, "run_bot", mock.Mock()) as run_mock:
            self.bot_scheduler.run_monthlys()
            compare(1, run_mock.call_count)
            self.assertTrue(isinstance(run_mock.mock_calls[0][1][0], self.Bot2))

    def test_run_monthly_nothing_to_do(self):
        self.bot_scheduler.monthly_bots = {1: [self.Bot1], 2: [self.Bot2]}
        self.now_mock.return_value = datetime(year=2010, month=1, day=3)
        with mock.patch.object(self.bot_scheduler, "run_bot", mock.Mock()) as run_mock:
            self.bot_scheduler.run_monthlys()
            compare(0, run_mock.call_count)

    def test_run_last_day_of_month(self):
        self.bot_scheduler.bots_on_last_day_of_month = [self.Bot1, self.Bot2]
        self.now_mock.return_value = datetime(year=2010, month=1, day=31)
        with mock.patch.object(self.bot_scheduler, "run_bot", mock.Mock()) as run_mock:
            self.bot_scheduler.run_monthlys()
            compare(2, run_mock.call_count)
            self.assertTrue(isinstance(run_mock.mock_calls[0][1][0], self.Bot1))
            self.assertTrue(isinstance(run_mock.mock_calls[1][1][0], self.Bot2))

    def test_empty_run(self):
        self.bot_scheduler.task()
