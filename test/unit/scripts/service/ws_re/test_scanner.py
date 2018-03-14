from datetime import datetime

from scripts.service.ws_re.scanner import ReScannerTask
from tools.bots import WikiLogger
from test import *

class TestReScannerTask(TestCase):
    class NAMETask(ReScannerTask):
        def task(self):
            pass

    class NAMEMoreExplanationTask(ReScannerTask):
        def task(self):
            pass

    def test_name(self):
        bot = self.NAMETask(None, WikiLogger(bot_name="Test", start_time=datetime(2000, 1, 1), silence=True))
        self.assertEqual("NAME", bot.get_name())
        bot = self.NAMEMoreExplanationTask(None, WikiLogger(bot_name="Test", start_time=datetime(2000, 1, 1), silence=True))
        self.assertEqual("NAME", bot.get_name())

    class MINITask(ReScannerTask):
        def task(self):
            pass

    def test_init_and_delete(self):
        with LogCapture() as log_catcher:
            task = self.MINITask(None, WikiLogger(bot_name="Test", start_time=datetime(2000, 1, 1), silence=True))
            log_catcher.check(("Test", "INFO", 'opening task MINI'))
            log_catcher.clear()
            del task
            log_catcher.check(("Test", "INFO", "closing task MINI"))