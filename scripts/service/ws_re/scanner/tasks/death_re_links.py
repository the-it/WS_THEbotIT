import re
from datetime import datetime

import pywikibot

from scripts.service.ws_re.scanner.tasks.error_handling import ERROTask
from scripts.service.ws_re.template.article import Article
from tools.bots import WikiLogger


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
