import datetime
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
        source_short_description = pywikibot.Page(self.wiki, "Wikisource:RE-Werkstatt/Kurzbeschreibung/a")

    def _load_source_short_description(self, source_text: str):

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
