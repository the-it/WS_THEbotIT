import re
from abc import abstractmethod
from datetime import timedelta
from typing import Optional

import pywikibot

from scripts.service.ws_re.template.re_page import RePage
from tools.bots import WikiLogger

SUCCESS = "success"
CHANGED = "changed"


class ReScannerTask:
    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        self.wiki = wiki
        self.debug = debug
        self.logger = logger
        self.re_page: Optional[RePage] = None
        self.processed_pages = []
        self.timeout = timedelta(minutes=1)
        self.load_task()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    def task(self):
        pass

    def run(self, re_page: RePage):
        self.re_page = re_page
        preprocessed_hash = hash(self.re_page)
        result = {SUCCESS: False, CHANGED: False}
        try:
            self.task()
        except Exception as exception:  # pylint: disable=broad-except
            self.logger.exception("Logging a caught exception", exception)
        else:
            result[SUCCESS] = True
            self.processed_pages.append(re_page.lemma)
        if preprocessed_hash != hash(self.re_page):
            result[CHANGED] = True
        return result

    def load_task(self):
        self.logger.info(f"opening task {self.name}")

    def finish_task(self):
        self.logger.info(f"closing task {self.name}")

    @property
    def name(self) -> str:
        return re.search("([A-Z0-9]{4})[A-Za-z]*?Task", str(self.__class__)).group(1)


class ReporterMixin:
    _wiki_page = "Wiki lemma to report to"
    _reason = "Reason to save report page"

    def __init__(self, report_wiki: pywikibot.Site):
        self.data = []
        self.report_wiki = report_wiki

    @abstractmethod
    def _build_entry(self):
        pass

    def _data_exists(self) -> bool:
        return bool(self.data)

    def report_data_entries(self):
        if self._data_exists():
            page = pywikibot.Page(self.report_wiki, self._wiki_page)
            page.text = page.text + self._build_entry()
            page.save(self._reason, botflag=True)
