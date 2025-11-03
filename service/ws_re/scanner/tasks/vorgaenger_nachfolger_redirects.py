import pywikibot

from service.ws_re.scanner.tasks.base_task import ReScannerTask
from service.ws_re.template.article import Article


class VONATask(ReScannerTask):
    """
    Check REDaten fields VORGÄNGER and NACHFOLGER.
    If they point to an RE redirect, rewrite to the redirect target (lemma without prefix).
    """

    def task(self) -> bool:
        for article in self.re_page:
            if not isinstance(article, Article):
                continue
            for key in ("VORGÄNGER", "NACHFOLGER"):
                value = article[key].value
                if not value:
                    continue
                page = pywikibot.Page(self.wiki, f"RE:{value}")
                if page.isRedirectPage():
                    target_title = page.getRedirectTarget().title()
                    # Strip RE: namespace if present
                    target_lemma = target_title[3:]
                    if target_lemma != value:
                        article[key].value = target_lemma
        return True
