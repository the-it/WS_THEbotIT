from datetime import datetime
from typing import Dict

import pywikibot

from service.ws_re.scanner.tasks.base_task import ReScannerTask, ReporterMixin
from service.ws_re.template.article import Article
from tools.bots.logger import WikiLogger


class DEWPTask(ReScannerTask, ReporterMixin):
    _wiki_page = "RE:Wartung:Tote Links nach Wikipedia"
    _reason = "Neue tote Links"

    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        ReScannerTask.__init__(self, wiki, logger, debug)
        ReporterMixin.__init__(self, wiki)
        self.wp_wiki = pywikibot.Site(code="de", fam="wikipedia", user="THEbotIT")
        self.data: Dict = {"not_exists": [], "redirect": [], "disambiguous": []}

    def task(self):  # pylint: disable=arguments-differ
        for article in self.re_page:
            reason = ""
            # check properties of REDaten Block first
            if isinstance(article, Article):
                link_to_check = article["WIKIPEDIA"].value
                if link_to_check:
                    page = pywikibot.Page(self.wp_wiki, link_to_check)
                    try:
                        if not page.exists():
                            reason = "not_exists"
                        elif page.isRedirectPage():
                            reason = "redirect"
                        elif page.isDisambig():
                            reason = "disambiguous"
                    except pywikibot.exceptions.InvalidTitleError:
                        reason = "not_exists"
                    if reason:
                        self.data[reason].append((link_to_check, self.re_page.lemma_without_prefix))
        return True

    def _build_entry(self) -> str:
        caption = f"\n\n=={datetime.now():%Y-%m-%d}==\n\n"
        entries = []
        for label in ("not_exists", "redirect", "disambiguous"):
            if self.data[label]:
                headline = "Artikel existieren in Wikipedia nicht"
                if label == "redirect":
                    headline = "Linkziel ist ein Redirect"
                elif label == "disambiguous":
                    headline = "Linkziel ist eine Begriffsklärungsseite"
                entries.append(f"=== {headline} ===")
                for item in self.data[label]:
                    if label == "not_exists":
                        entries.append(f"* Wikpedia Artikel: [[w:{item[0]}]] (verlinkt von [[RE:{item[1]}]]) "
                                       f"existiert nicht")
                    elif label == "redirect":
                        entries.append(f"* Wikpedia Artikel: [[w:{item[0]}]] (verlinkt von [[RE:{item[1]}]]) "
                                       f"ist ein Redirect")
                    elif label == "disambiguous":
                        entries.append(f"* Wikpedia Artikel: [[w:{item[0]}]] (verlinkt von [[RE:{item[1]}]]) "
                                       f"ist eine Begriffsklärungsseite")
        body = "\n".join(entries)
        return caption + body

    def _data_exists(self) -> bool:
        return bool(self.data["not_exists"]) or bool(self.data["redirect"]) or bool(self.data["disambiguous"])

    def finish_task(self):
        self.report_data_entries()
        super().finish_task()
