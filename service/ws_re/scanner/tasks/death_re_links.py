import re
from datetime import datetime
from typing import cast

import pywikibot

from service.ws_re.register.lemma import Lemma
from service.ws_re.scanner.tasks.base_task import ReScannerTask, ReporterMixin
from service.ws_re.template.article import Article
from tools.bots.logger import WikiLogger


class DEALTask(ReScannerTask, ReporterMixin):
    _wiki_page = "RE:Wartung:Tote Links"
    _reason = "Neue tote Links"

    _start_characters = ("a",
                         "b",
                         "c",
                         "d",
                         )

    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        ReScannerTask.__init__(self, wiki, logger, debug)
        ReporterMixin.__init__(self, wiki)
        regex_start_characters = ''.join(self._start_characters)
        regex_start_characters = regex_start_characters + regex_start_characters.upper()
        self.re_siehe_regex = re.compile(rf"(?:\{{\{{RE siehe\||\[\[RE:)"
                                         rf"([{regex_start_characters}][^\|\}}\]]+)")

    def task(self):
        for article in self.re_page:
            # check properties of REDaten Block first
            if isinstance(article, Article):
                for prop in ["VORGÄNGER", "NACHFOLGER"]:
                    # VORGÄNGER NACHFOLGER are string properties
                    link_to_check = cast(str, article[prop].value)
                    if link_to_check:
                        self._check_link(link_to_check)
                # then links in text
                for idx, potential_link in enumerate(self.re_siehe_regex.findall(article.text)):
                    # todo: do this with async tools, but for the moment check only the first 50 links
                    # relevant for RE:Register (Band XI)
                    if idx > 50:
                        break
                    self._check_link(potential_link)
            elif isinstance(article, str):
                for potential_link in self.re_siehe_regex.findall(article):
                    self._check_link(potential_link)
        return True

    def _check_link(self, link_to_check: str):
        if Lemma.make_sort_key(link_to_check)[0].lower() in self._start_characters:
            if not pywikibot.Page(self.wiki, f"RE:{link_to_check}").exists():
                self.data.append((link_to_check, self.re_page.lemma_without_prefix))

    def _build_entry(self) -> str:
        caption = f"\n\n=={datetime.now():%Y-%m-%d}==\n\n"
        entries = []
        for item in self.data:
            entries.append(f"* [[RE:{item[0]}]] verlinkt von [[RE:{item[1]}]]")
        body = "\n".join(entries)
        return caption + body

    def finish_task(self):
        self.report_data_entries()
        super().finish_task()
