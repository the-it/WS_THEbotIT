import re
from typing import Dict

import pywikibot

from service.ws_re.register.registers import RE_ALPHABET
from service.ws_re.scanner.tasks.base_task import ReScannerTask
from service.ws_re.template.article import Article
from tools.bots.pi import WikiLogger


class KURZTask(ReScannerTask):
    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        super().__init__(wiki, logger, debug)
        self.short_description_lookup: Dict[str, str] = {}

    def _get_short_description_text_from_source(self, starting_letter: str) -> str:
        text = pywikibot.Page(self.wiki, f"Wikisource:RE-Werkstatt/Kurzbeschreibung/{starting_letter}").text
        if not text:
            raise ValueError(f"There is no contenten on Wikisource:RE-Werkstatt/Kurzbeschreibung/{starting_letter}")
        return text

    @staticmethod
    def _load_source_short_description(source_text: str) -> Dict[str,str]:
        new_lookup_dict: Dict[str, str] = {}
        # splitting up by line and processing only the relevant lines from the table
        for line in source_text.strip().splitlines()[4::2]:
            # first group is the lemma, second is the description
            match = re.search(r"\[\[RE:([^\]]*?)\]\]\|\|(.*)", line)
            # don't process if there is an invalid description
            if match.group(2) != "(-)":
                new_lookup_dict[match.group(1)] = match.group(2)
        return new_lookup_dict

    def task(self):
        for re_article in self.re_page:
            if isinstance(re_article, Article):
                if re_article["KEINE_SCHÖPFUNGSHÖHE"].value:
                    if todesjahr := re_article["TODESJAHR"].value:
                        if int(todesjahr) <= self.pd_todesjahr:
                            re_article["TODESJAHR"].value = ""
                            re_article["KEINE_SCHÖPFUNGSHÖHE"].value = False
                    if geburtsjahr := re_article["GEBURTSJAHR"].value:
                        if int(geburtsjahr) <= self.pd_geburtsjahr:
                            re_article["GEBURTSJAHR"].value = ""
                            re_article["KEINE_SCHÖPFUNGSHÖHE"].value = False
