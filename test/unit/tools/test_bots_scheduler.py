from datetime import datetime

from test import *
from tools.bot_scheduler import BotScheduler

class TestBotScheduler(TestCase):
    def setUp(self):
        self.addCleanup(patch.stopall)
        self.now_patcher = patch("tools.bot_scheduler.BotScheduler.now", new_callable=mock.Mock())
        self.now_mock = self.now_patcher.start()
        self.bot_scheduler = BotScheduler(None, True)

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
