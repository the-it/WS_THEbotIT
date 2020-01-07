# pylint: disable=protected-access,no-member,no-self-use
import os
from datetime import datetime
from unittest import TestCase

from testfixtures import compare

from tools.bots.cloud.base import TMP_WIKI_BOT_PATH
from tools.bots.cloud.logger import WikiLogger
from tools.bots.cloud.test_base import teardown_data_path, setup_data_path


class TestWikilogger(TestCase):
    def setUp(self):
        setup_data_path()
        self.logger = WikiLogger("test_bot", datetime(year=2000, month=1, day=1), log_to_screen=False)
        self.logger.__enter__()

    def tearDown(self):
        self.logger.tear_down()
        teardown_data_path()

    def test_logfile_names(self):
        compare("test_bot_INFO_000101000000.log", self.logger._get_logger_name())

    def test_log_message(self):
        self.logger.debug("debug")
        self.logger.info("info")
        with open(TMP_WIKI_BOT_PATH + os.sep + "test_bot_INFO_000101000000.log") as info_file:
            self.assertRegex(info_file.read(), r"\[\d\d:\d\d:\d\d\]\s\[INFO\s*?\]\s\[info\]\n")

    def test_tear_down(self):
        self.logger.debug("debug")
        self.logger.info("info")
        self.assertTrue(os.path.isfile(TMP_WIKI_BOT_PATH + os.sep + "test_bot_INFO_000101000000.log"))
        self.logger.tear_down()
        self.assertFalse(os.path.isfile(TMP_WIKI_BOT_PATH + os.sep + "test_bot_INFO_000101000000.log"))

    def test_format_log_lines_for_wiki(self):
        self.logger.info("info")
        self.logger.warning("warning")
        self.logger.error("error")
        self.logger.critical("critical")
        expected_output = r"==00-01-01_00:00:00==\n\n" \
                          r"\[\d\d:\d\d:\d\d\]\s\[INFO\s*?\]\s\[info\]\n\n" \
                          r"\[\d\d:\d\d:\d\d\]\s\[WARNING\s*?\]\s\[warning\]\n\n" \
                          r"\[\d\d:\d\d:\d\d\]\s\[ERROR\s*?\]\s\[error\]\n\n" \
                          r"\[\d\d:\d\d:\d\d\]\s\[CRITICAL\s*?\]\s\[critical\]\n--~~~~"
        self.assertRegex(self.logger.create_wiki_log_lines(), expected_output)

    def test_exception(self):
        self.logger.exception("exception", Exception("test"))
        expected_output = r"==00-01-01_00:00:00==\n\n" \
                          r"\[\d\d:\d\d:\d\d\]\s\[ERROR\s*?\]\s\[exception\]\n\n" \
                          r"Exception: test\n--~~~~"
        self.assertRegex(self.logger.create_wiki_log_lines(), expected_output)
