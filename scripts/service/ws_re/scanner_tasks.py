import logging
import re
from abc import abstractmethod
from datetime import timedelta, datetime
from typing import Mapping

from pywikibot import Site, Page

from scripts.service.ws_re.data_types import RePage, Article
from scripts.service.ws_re.register import Registers, Authors, AuthorCrawler
from tools import fetch_text_from_wiki_site
from tools.bots import WikiLogger

SUCCESS = "success"
CHANGED = "changed"


class ReScannerTask:
    def __init__(self, wiki: Site, logger: WikiLogger, debug: bool = True):
        self.wiki = wiki
        self.debug = debug
        self.logger = logger
        self.re_page = None  # type: RePage
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
        self.logger.info('opening task {}'.format(self.get_name()))

    def finish_task(self):
        self.logger.info('closing task {}'.format(self.get_name()))

    def get_name(self):
        return re.search("([A-Z0-9]{4})[A-Za-z]*?Task", str(self.__class__)).group(1)


class ERROTask(ReScannerTask):
    def __init__(self, wiki: Site, logger: WikiLogger, debug: bool = True):
        super().__init__(wiki, logger, debug)
        self.data = []

    def task(self, lemma: str, reason: str):  # pylint: disable=arguments-differ
        self.data.append((lemma, reason))

    def _build_entry(self) -> str:
        caption = "\n\n=={}==\n\n".format(datetime.now().strftime("%Y-%m-%d"))
        entries = []
        for item in self.data:
            entries.append("* [[{lemma}]]\n** {reason}".format(lemma=item[0], reason=item[1]))
        body = "\n".join(entries)
        return caption + body

    def finish_task(self):
        if self.data:
            if not self.debug:
                page = Page(self.wiki, "RE:Wartung:Strukturfehler")
                page.text = page.text + self._build_entry()
                page.save("Neue Fehlermeldungen", botflag=True)
        super().finish_task()


class KSCHTask(ReScannerTask):
    _regex_template = re.compile(r"{{RE keine Schöpfungshöhe\|(\d\d\d\d)}}")

    def task(self):
        for re_article in self.re_page:
            if isinstance(re_article, Article):
                template_match = self._regex_template.search(re_article.text)
                if template_match:
                    re_article["TODESJAHR"].value = template_match.group(1)
                    re_article["KEINE_SCHÖPFUNGSHÖHE"].value = True
                    re_article.text = self._regex_template.sub("", re_article.text).strip()


class VERWTask(ReScannerTask):
    _regex_template = re.compile(r"\[\[Kategorie:RE:Verweisung\|?[^\]]*\]\]")

    def task(self):
        for re_article in self.re_page:
            if isinstance(re_article, Article):
                template_match = self._regex_template.search(re_article.text)
                if template_match:
                    re_article["VERWEIS"].value = True
                    re_article.text = self._regex_template.sub("", re_article.text).strip()


class SCANTask(ReScannerTask):
    def __init__(self, wiki: Site, logger: WikiLogger, debug: bool = True):
        super().__init__(wiki, logger, debug)
        self.registers = None  # type: Registers

    def task(self):
        pass

    def load_task(self):
        super().load_task()
        self.logger.info("Loading special task")

    def finish_task(self):
        super().finish_task()
        authors = Authors()
        authors.set_mappings(self._fetch_mapping())
        authors.set_author(self._fetch_author_infos())
        authors.persist()

    def _fetch_author_infos(self) -> Mapping:
        text = fetch_text_from_wiki_site(self.wiki,
                                         "Paulys Realencyclopädie der classischen "
                                         "Altertumswissenschaft/Autoren")
        return AuthorCrawler.get_authors(text)

    def _fetch_mapping(self) -> Mapping:
        text = fetch_text_from_wiki_site(self.wiki, "Modul:RE/Autoren")
        return AuthorCrawler.get_mapping(text)


if __name__ == "__main__":
    WS_WIKI = Site(code='de', fam='wikisource', user='THEbotIT')
    LOGGER = logging.getLogger("test")
    SCANTask(WS_WIKI, LOGGER).finish_task()
