import re
from abc import abstractmethod
from datetime import timedelta, datetime

import pywikibot

from scripts.service.ws_re.data_types import RePage, Article
from tools.bots import WikiLogger

SUCCESS = "success"
CHANGED = "changed"


class ReScannerTask:
    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
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
        self.logger.info(f"opening task {self.name}")

    def finish_task(self):
        self.logger.info(f"closing task {self.name}")

    @property
    def name(self):
        return re.search("([A-Z0-9]{4})[A-Za-z]*?Task", str(self.__class__)).group(1)


class ERROTask(ReScannerTask):
    _wiki_page = "RE:Wartung:Strukturfehler"
    _reason = "Neue Fehlermeldungen"

    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        super().__init__(wiki, logger, debug)
        self.data = []

    def task(self, lemma: str, reason: str):  # pylint: disable=arguments-differ
        self.data.append((lemma, reason))

    def _build_entry(self) -> str:
        caption = f"\n\n=={datetime.now():%Y-%m-%d}==\n\n"
        entries = []
        for item in self.data:
            entries.append(f"* [[{item[0]}]]\n** {item[1]}")
        body = "\n".join(entries)
        return caption + body

    def finish_task(self):
        if self.data:
            if not self.debug:
                page = pywikibot.Page(self.wiki, self._wiki_page)
                page.text = page.text + self._build_entry()
                page.save(self._reason, botflag=True)
        super().finish_task()


class DEALTask(ERROTask):
    _wiki_page = "RE:Wartung:Tote Links"
    _reason = "Neue tote Links"

    _start_characters = ("a",
                         "b",
                         "c",
                         )

    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        super().__init__(wiki, logger, debug)
        regex_start_characters = ''.join(self._start_characters)
        regex_start_characters = regex_start_characters + regex_start_characters.upper()
        self.re_siehe_regex = re.compile(rf"(?:\{{\{{RE siehe\||\[\[RE:)"
                                         rf"([{regex_start_characters}][^\|\}}\]]+)")

    def task(self):  # pylint: disable=arguments-differ
        for article in self.re_page:
            # check properties of REDaten Block first
            if isinstance(article, Article):
                for prop in ["VORGÄNGER", "NACHFOLGER"]:
                    link_to_check = article[prop].value
                    if link_to_check:
                        self._check_link(link_to_check)
                # then links in text
                for potential_link in self.re_siehe_regex.findall(article.text):
                    self._check_link(potential_link)
            elif isinstance(article, str):
                for potential_link in self.re_siehe_regex.findall(article):
                    self._check_link(potential_link)
        return True

    def _check_link(self, link_to_check):
        if link_to_check[0].lower() in self._start_characters:
            if not pywikibot.Page(self.wiki, f"RE:{link_to_check}").exists():
                self.data.append((link_to_check, self.re_page.lemma_without_prefix))

    def _build_entry(self) -> str:
        caption = f"\n\n=={datetime.now():%Y-%m-%d}==\n\n"
        entries = []
        for item in self.data:
            entries.append(f"* [[RE:{item[0]}]] verlinkt von [[RE:{item[1]}]]")
        body = "\n".join(entries)
        return caption + body


class DEWPTask(ERROTask):
    _wiki_page = "RE:Wartung:Tote Links nach Wikipedia"
    _reason = "Neue tote Links"

    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        super().__init__(wiki, logger, debug)
        self.wp_wiki = pywikibot.Site(code="de", fam="wikipedia", user="THEbotIT")

    def task(self):  # pylint: disable=arguments-differ
        for article in self.re_page:
            # check properties of REDaten Block first
            if isinstance(article, Article):
                link_to_check = article["WIKIPEDIA"].value
                if link_to_check:
                    page = pywikibot.Page(self.wp_wiki, link_to_check)
                    if page.exists():
                        if not page.isRedirectPage():
                            continue
                    self.data.append((link_to_check, self.re_page.lemma_without_prefix))
        return True

    def _build_entry(self) -> str:
        caption = f"\n\n=={datetime.now():%Y-%m-%d}==\n\n"
        entries = []
        for item in self.data:
            entries.append(f"* Wikpedia Artikel: [[w:{item[0]}]] verlinkt von [[RE:{item[1]}]] "
                           f"existiert nicht")
        body = "\n".join(entries)
        return caption + body


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
