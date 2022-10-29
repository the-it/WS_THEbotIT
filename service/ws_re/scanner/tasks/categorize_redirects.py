import re

import pywikibot

from service.ws_re.scanner.tasks.base_task import ReScannerTask
from tools.bots.pi import WikiLogger
from tools.utils import save_if_changed


class CARETask(ReScannerTask):
    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        ReScannerTask.__init__(self, wiki, logger, debug)

    def task(self) -> bool:
        for redirect in self.re_page.get_redirects():
            save_if_changed(redirect, self.add_redirect_category(redirect.text), "füge Kategorie für RE:Redirect ein.")
        return True

    @staticmethod
    def add_redirect_category(text: str) -> str:
        if not re.search(r"\[\[Kategorie:RE:Redirect", text):
            return text + "\n[[Kategorie:RE:Redirect]]"
        return text
