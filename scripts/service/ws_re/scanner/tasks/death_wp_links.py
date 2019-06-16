from datetime import datetime

import pywikibot

from scripts.service.ws_re.scanner.tasks.error_handling import ERROTask
from scripts.service.ws_re.template.article import Article
from tools.bots import WikiLogger


class DEWPTask(ERROTask):
    _wiki_page = "RE:Wartung:Tote Links nach Wikipedia"
    _reason = "Neue tote Links"

    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        super().__init__(wiki, logger, debug)
        self.wp_wiki = pywikibot.Site(code="de", fam="wikipedia", user="THEbotIT")
        self.data = {"not_exists": [], "redirect": []}

    def task(self):  # pylint: disable=arguments-differ
        for article in self.re_page:
            # check properties of REDaten Block first
            if isinstance(article, Article):
                link_to_check = article["WIKIPEDIA"].value
                if link_to_check:
                    page = pywikibot.Page(self.wp_wiki, link_to_check)
                    reason = "not_exists"
                    if page.exists():
                        if not page.isRedirectPage():
                            continue
                        reason = "redirect"
                    self.data[reason].append((link_to_check, self.re_page.lemma_without_prefix))
        return True

    def _build_entry(self) -> str:
        caption = f"\n\n=={datetime.now():%Y-%m-%d}==\n\n"
        entries = []
        for label in ("not_exists", "redirect"):
            if self.data[label]:
                entries.append("=== Artikel existieren in Wikipedia nicht ==="
                               if label == "not_exists"
                               else "=== Linkziel ist ein Redirect ===")
                for item in self.data[label]:
                    if label == "not_exists":
                        entries.append(f"* Wikpedia Artikel: [[w:{item[0]}]] (verlinkt von [[RE:{item[1]}]]) "
                                       f"existiert nicht")
                    else:
                        entries.append(f"* Wikpedia Artikel: [[w:{item[0]}]] (verlinkt von [[RE:{item[1]}]]) "
                                       f"ist ein Redirect")
        body = "\n".join(entries)
        return caption + body

    def _data_exists(self):
        return bool(self.data["not_exists"]) or bool(self.data["redirect"])
