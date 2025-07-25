import re
from typing import Dict

import pywikibot

from service.ws_re.register.lemma import Lemma
from service.ws_re.register.registers import RE_ALPHABET
from service.ws_re.scanner.tasks.base_task import ReScannerTask
from tools.bots.logger import WikiLogger


class KURZTask(ReScannerTask):
    MAINTENANCE_CAT = "RE:Kurztext überprüfen"
    SHORT_TEXT_URL = "Wikisource:RE-Werkstatt/Kurzbeschreibung/"

    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        super().__init__(wiki, logger, debug)
        self.short_description_lookup: Dict[str, str] = self._load_short_descriptions()

    def _get_short_description_text_from_source(self, starting_letter: str) -> str:
        text: str = pywikibot.Page(self.wiki, f"{self.SHORT_TEXT_URL}{starting_letter}").text
        if not text:
            raise ValueError(f"There is no content on {self.SHORT_TEXT_URL}{starting_letter}")
        return text

    def _load_short_descriptions(self):
        complete_descriptions_dict = {}
        for letter in RE_ALPHABET:
            try:
                complete_descriptions_dict.update(
                    self._parse_short_description(self._get_short_description_text_from_source(letter)))
            except ValueError:
                self.logger.error(f"Couldn't load {self.SHORT_TEXT_URL}{letter}.")
        return complete_descriptions_dict

    @staticmethod
    def _parse_short_description(source_text: str) -> Dict[str, str]:
        new_lookup_dict: Dict[str, str] = {}
        # splitting up by line and processing only the relevant lines from the table
        for line in source_text.strip().splitlines()[4::2]:
            # first group is the lemma, second is the description
            match = re.search(r"\[\[RE:([^\]]*?)\]\]\|\|(.*)", line)
            # don't process if there is an invalid description
            if match:
                if match.group(2) not in ["", "(-)"]:
                    new_lookup_dict[Lemma.make_sort_key(match.group(1))] = match.group(2)
        return new_lookup_dict

    def task(self):
        article = self.re_page.first_article
        if article["VERWEIS"].value:
            return
        if article["KURZTEXT"].value:
            return
        try:
            article["KURZTEXT"].value = \
                self.short_description_lookup[Lemma.make_sort_key(self.re_page.lemma_without_prefix)]
            self.re_page.add_error_category(category=self.MAINTENANCE_CAT)
        except KeyError:
            pass
