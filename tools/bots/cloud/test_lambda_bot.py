# pylint: disable=protected-access,no-member,no-self-use
import time
from datetime import timedelta
from unittest import mock

from testfixtures import LogCapture, compare

from tools.bots.cloud.lambda_bot import LambdaBot
from tools.bots.cloud.test_base import setup_data_path, teardown_data_path, TestCloudBase
from tools.bots.cloud.logger import WikiLogger


class TestLambdaBot(TestCloudBase):
    def setUp(self):
        super().setUp()
        setup_data_path()
        self.addCleanup(mock.patch.stopall)
        self.log_patcher = mock.patch.object(WikiLogger, "debug")
        self.wiki_logger_mock = self.log_patcher.start()

    def tearDown(self):
        teardown_data_path()
        super().tearDown()

    class MinimalBot(LambdaBot):
        def task(self):
            pass

    def test_get_bot_name(self):
        self.assertEqual("MinimalBot", self.MinimalBot.get_bot_name())
        self.assertEqual("MinimalBot", self.MinimalBot().bot_name)

    # pylint: disable=abstract-method
    class NoTaskBot(LambdaBot):
        pass

    def test_not_implemented(self):
        # pylint: disable=abstract-class-instantiated
        with self.assertRaises(TypeError):
            self.NoTaskBot()

    def test_basic_run(self):
        with self.MinimalBot(log_to_screen=False, log_to_wiki=False) as bot:
            bot.run()

    class LogBot(LambdaBot):
        def task(self):
            self.logger.info("Test")
            time.sleep(0.001)

    class SuccessBot(LambdaBot):
        def __init__(self, success=True, **kwargs):
            super().__init__(**kwargs)
            self.success_to_return = success

        def task(self):
            return self.success_to_return

    def test_return_value_run(self):
        with self.SuccessBot(success=True, log_to_screen=False, log_to_wiki=False) as bot:
            self.assertTrue(bot.run())

        with self.SuccessBot(success=False, log_to_screen=False, log_to_wiki=False) as bot:
            self.assertFalse(bot.run())

    def test_logging(self):
        with LogCapture() as log_catcher:
            log_catcher.clear()
            with self.LogBot(log_to_screen=False, log_to_wiki=False) as bot:
                # logging on enter
                # log_catcher.check(("LogBot", "INFO", "Start the bot LogBot."))
                log_catcher.clear()
                bot.run()
                # logging on run
                log_catcher.check(("LogBot", "INFO", "Test"))
                log_catcher.clear()
            # logging on exit
            self.assertRegex(str(log_catcher), r"LogBot INFO\n  Finish bot LogBot in 0:00:00.\d{6}.")

    def test_watchdog(self):
        class WatchdogBot(LambdaBot):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.timeout = timedelta(seconds=0.1)

            def task(self):
                while True:
                    if self._watchdog():
                        raise Exception("watchdog must not fire")  # pragma: no cover
                    time.sleep(0.1)
                    if self._watchdog():
                        return True
                    raise Exception("watchdog must fire")  # pragma: no cover

        with WatchdogBot(log_to_screen=False, log_to_wiki=False) as bot:
            self.assertTrue(bot.run())

    def test_send_log_to_wiki(self):
        with mock.patch("tools.bots.cloud.lambda_bot.Page") as mock_page:
            with self.MinimalBot(wiki=None, log_to_screen=False) as bot:
                bot.run()
            self.assertEqual(mock.call(None, "Benutzer:THEbotIT/Logs/MinimalBot"), mock_page.mock_calls[0])
            self.assertEqual(mock.call().text.__iadd__(mock.ANY), mock_page.mock_calls[1])
            self.assertEqual(mock.call().save("Update of Bot MinimalBot", botflag=True),
                             mock_page.mock_calls[2])

    def test_save_if_changed_positive(self):
        page_mock = mock.Mock()
        text_mock = mock.PropertyMock()
        type(page_mock).text = text_mock
        text_mock.return_value = "2"
        self.MinimalBot.save_if_changed(page_mock, "1", "changed")
        compare(mock.call.save("changed", botflag=True), page_mock.mock_calls[0])

    def test_save_if_changed_negativ(self):
        page_mock = mock.Mock()
        text_mock = mock.PropertyMock()
        type(page_mock).text = text_mock
        text_mock.return_value = "1"
        self.MinimalBot.save_if_changed(page_mock, "1", "changed")
        compare(0, len(page_mock.mock_calls))

        self.MinimalBot.save_if_changed(page_mock, "1 ", "changed")
        compare(0, len(page_mock.mock_calls))

    class ExceptionBot(LambdaBot):
        def task(self):
            raise Exception("Exception")

    def test_throw_exception_in_task(self):
        with LogCapture() as log_catcher:
            with self.ExceptionBot(log_to_screen=False, log_to_wiki=False) as bot:
                log_catcher.clear()
                bot.run()
                log_catcher.check(("ExceptionBot", "ERROR", "Logging an uncaught exception"))
                self.assertFalse(bot.success)
