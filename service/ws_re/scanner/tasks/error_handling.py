from datetime import datetime

import pywikibot

from service.ws_re.scanner.scanner import ReScannerTask
from service.ws_re.scanner.tasks.base_task import ReporterMixin
from tools.bots.pi import WikiLogger


class ERROTask(ReScannerTask, ReporterMixin):
    _wiki_page = "RE:Wartung:Strukturfehler"
    _reason = "Neue Fehlermeldungen"

    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        ReScannerTask.__init__(self, wiki, logger, debug)
        ReporterMixin.__init__(self, wiki)

    def task(self):
        pass

    def append_error(self, lemma: str, reason: str):
        self.data.append((lemma, reason))

    def _build_entry(self) -> str:
        caption = f"\n\n=={datetime.now():%Y-%m-%d}==\n\n"
        entries = []
        for item in self.data:
            entries.append(f"* [[{item[0]}]]\n** {item[1]}")
        body = "\n".join(entries)
        return caption + body

    def finish_task(self):
        self.report_data_entries()
        super().finish_task()
