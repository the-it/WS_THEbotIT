from datetime import datetime

import pywikibot

from scripts.service.ws_re.scanner import ReScannerTask
from tools.bots import WikiLogger


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
