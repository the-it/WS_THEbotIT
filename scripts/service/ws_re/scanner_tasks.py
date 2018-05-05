import re
from abc import abstractmethod
from datetime import timedelta, datetime

from pywikibot import Site

from scripts.service.ws_re.data_types import RePage
from tools.bots import WikiLogger

SUCCESS = "success"
CHANGED = "changed"


class ReScannerTask(object):
    def __init__(self, wiki: Site, logger: WikiLogger, debug: bool = True):
        self.wiki = wiki
        self.debug = debug
        self.logger = logger
        self.re_page = None  # type: RePage
        self.result = {SUCCESS: False, CHANGED: False}
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
        try:
            self.task()
        except Exception as exception:  # pylint: disable=broad-except
            self.logger.exception("Logging a caught exception", exception)
        else:
            self.result[SUCCESS] = True
            self.processed_pages.append(re_page.lemma)
        if preprocessed_hash != hash(self.re_page):
            self.result[CHANGED] = True
        return self.result

    def load_task(self):
        self.logger.info('opening task {}'.format(self.get_name()))

    def finish_task(self):
        self.logger.info('closing task {}'.format(self.get_name()))

    def get_name(self):
        return re.search("([A-Z0-9]{4})[A-Za-z]*?Task", str(self.__class__)).group(1)


class ERROTask(ReScannerTask):
    def __init__(self, wiki: Site, logger: WikiLogger, debug: bool = True):
        super().__init__(wiki, logger, debug)
        self.data = []

    def task(self, lemma: str):  # pylint: disable=arguments-differ
        self.logger.error("Lemma {} is registered, because the structure was wrong.".format(lemma))
        self.data.append(lemma)

    def _build_entry(self) -> str:
        caption = "=={}==\n\n".format(datetime.now().strftime("%Y-%m-%d"))
        body = "* [[" + "]]\n* [[".join(self.data) + "]]\n"
        return caption + body

    # def finish_task(self):
    #     super().finish_task()
