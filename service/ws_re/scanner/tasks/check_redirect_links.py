import re

import pywikibot

from service.ws_re.scanner.tasks.base_task import ReScannerTask
from tools.bots.pi import WikiLogger


class CHRETask(ReScannerTask):
    error_category = "RE:Links führen auf Redirects"

    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        ReScannerTask.__init__(self, wiki, logger, debug)
        self.filter_regex = re.compile(
            r"(Benutzer:S8w4|"
            r"Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/|"
            r"Wikisource:RE-Werkstatt/"
            r").*"
        )

    def task(self) -> bool:
        for redirect in self.re_page.get_redirects():
            filtered_list = self.filter_link_list(self.get_backlinks(redirect))
            if filtered_list:
                self.re_page.add_error_category(self.error_category)
                return True
        self.re_page.remove_error_category(self.error_category)
        return True

    @staticmethod
    def get_backlinks(redirect_page: pywikibot.Page) -> list[str]:
        return [page.title() for page in redirect_page.backlinks()]

    def filter_link_list(self, link_list: list[str]) -> list[str]:
        return [link for link in link_list if self.filter_regex.search(link) is None]
