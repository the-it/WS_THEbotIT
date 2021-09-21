import logging
import os
import sys
import tempfile
from datetime import datetime


class WikiLogger():
    _logger_format: str = "[%(asctime)s] [%(levelname)-8s] [%(message)s]"
    _logger_date_format: str = "%H:%M:%S"
    _wiki_timestamp_format: str = "%y-%m-%d_%H:%M:%S"

    def __init__(self, bot_name: str, start_time: datetime, log_to_screen: bool = True):
        self._bot_name: str = bot_name
        self._start_time: datetime = start_time
        self._data_path: str = tempfile.mkdtemp()
        self._logger: logging.Logger = logging.getLogger(self._bot_name)
        self._logger_name: str = self._get_logger_name()
        self._log_to_screen: bool = log_to_screen

    def __enter__(self):
        self._setup_logger_properties()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.tear_down()

    def tear_down(self):
        for handler in self._logger.handlers[:]:
            handler.close()
            self._logger.removeHandler(handler)
        if os.path.isfile(self._data_path + os.sep + self._logger_name):
            os.remove(self._data_path + os.sep + self._logger_name)
        sys.stdout.flush()
        logging.shutdown()

    def _get_logger_name(self) -> str:
        start_time = self._start_time.strftime('%y%m%d%H%M%S')
        return f"{self._bot_name}_INFO_{start_time}.log"

    def _setup_logger_properties(self):
        self._logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(self._logger_format, datefmt=self._logger_date_format)
        error_log = logging.FileHandler(self._data_path + os.sep + self._logger_name, encoding="utf8")
        error_log.setLevel(logging.INFO)
        error_log.setFormatter(formatter)
        self._logger.addHandler(error_log)
        if self._log_to_screen:  # pragma: no cover
            # this activates the output of the logger
            debug_stream = logging.StreamHandler(sys.stdout)
            debug_stream.setLevel(logging.DEBUG)
            debug_stream.setFormatter(formatter)
            self._logger.addHandler(debug_stream)

    def debug(self, msg: str):
        self._logger.log(logging.DEBUG, msg)

    def info(self, msg: str):
        self._logger.log(logging.INFO, msg)

    def warning(self, msg: str):
        self._logger.log(logging.WARNING, msg)

    def error(self, msg: str):
        self._logger.log(logging.ERROR, msg)

    def critical(self, msg: str):
        self._logger.log(logging.CRITICAL, msg)

    def exception(self, msg: str, exc_info):
        self._logger.exception(msg=msg, exc_info=exc_info)

    def create_wiki_log_lines(self) -> str:
        with open(self._data_path + os.sep + self._logger_name, encoding="utf8") as filepointer:
            line_list = []
            for line in filepointer:
                line_list.append(line.strip())
            log_lines = ""
            log_lines = log_lines \
                + "\n\n" \
                + f"=={self._start_time.strftime(self._wiki_timestamp_format)}==" \
                + "\n\n" \
                + "\n\n".join(line_list) \
                + "\n--~~~~"
            return log_lines
