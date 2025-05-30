from datetime import datetime

import pywikibot

from service.ws_re.scanner.tasks.base import get_redirect
from service.ws_re.scanner.tasks.base_task import ReScannerTask, ReporterMixin
from tools.bots.cloud.logger import WikiLogger


class WAORTask(ReScannerTask, ReporterMixin):
    _wiki_page = "RE:Wartung:Artikel sind in der falschen Reihenfolge"
    _reason = "Neue Lemma gefunden"

    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        ReScannerTask.__init__(self, wiki, logger, debug)
        ReporterMixin.__init__(self, wiki)

    def task(self):
        # just one article, nothing to check
        if len(self.re_page.splitted_article_list) == 1:
            return
        # first article isn't a VERWEIS. First article is a relevant article
        if not self.re_page.splitted_article_list.first_article["VERWEIS"].value:
            return
        # article redirects to another lemma
        if isinstance(get_redirect(self.re_page.first_article), str):
            return
        for sub_article_list in self.re_page.splitted_article_list.list[1:]:
            if not sub_article_list.daten["VERWEIS"].value and len(sub_article_list.daten.text) > 100:
                self.data.append(self.re_page.lemma)
                break

    def _build_entry(self) -> str:
        caption = f"\n\n=={datetime.now():%Y-%m-%d}==\n\n"
        entries = []
        for item in self.data:
            entries.append(f"* [[{item}]]")
        body = "\n".join(entries)
        return caption + body

    def finish_task(self):
        self.report_data_entries()
        super().finish_task()
