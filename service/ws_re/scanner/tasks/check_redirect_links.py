import re
import time

import pywikibot

from service.ws_re.scanner.tasks.base_task import ReScannerTask
from tools import save_if_changed
from tools.bots.pi import WikiLogger


REGEX_TRANSLATION = str.maketrans({"(": r"\(",
                                   ")": r"\)",
                                   "?": r"\?"})

class CHRETask(ReScannerTask):
    error_category = "RE:Links führen auf Redirects"

    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        ReScannerTask.__init__(self, wiki, logger, debug)
        self.filter_regex = re.compile(
            r"(Benutzer|"
            r"Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/|"
            r"Wikisource:"
            r").*"
        )

    def task(self) -> bool:
        self.iterate_throw_redirects(repair=True)
        self.iterate_throw_redirects(report=True)
        return True

    def iterate_throw_redirects(self, repair: bool = False, report: bool = False):
        for redirect in self.re_page.get_redirects():
            filtered_list = self.filter_link_list(self.get_backlinks(redirect))
            if filtered_list:
                if repair:
                    self.rename_redirects_to_target(filtered_list, redirect)
                    time.sleep(2)
                if report:
                    self.re_page.add_error_category(self.error_category)
                    return
        self.re_page.remove_error_category(self.error_category)

    def rename_redirects_to_target(self, filtered_list: list[str], redirect: pywikibot.Page):
        for entry in filtered_list:
            page = pywikibot.Page(self.wiki, entry)
            new_text = self.replace_redirect_links(page.text, redirect.title()[3:], self.re_page.lemma_without_prefix)
            save_if_changed(page, new_text, f"Link korrigiert von {redirect} zu {self.re_page.page}")

    @staticmethod
    def get_backlinks(redirect_page: pywikibot.Page) -> list[str]:
        return [page.title() for page in redirect_page.backlinks()]

    def filter_link_list(self, link_list: list[str]) -> list[str]:
        return [link for link in link_list if self.filter_regex.search(link) is None]



    @staticmethod
    def replace_redirect_links(text: str, redirect: str, target: str):
        redirect_re = redirect.translate(REGEX_TRANSLATION)
        # [[RE:Redirect]] -> [[RE:Target]], [[RE:Redirect|Something]] -> [[RE:Target|Something]]
        temp_text = re.sub(rf"\[\[RE:{redirect_re}(\||\]\])", rf"[[RE:{target}\g<1>", text)
        # {{RE siehe|Redirect}} -> {{RE siehe|Target|Redirect}}
        temp_text = re.sub(rf"{{RE siehe\|{redirect_re}}}", f"{{RE siehe|{target}|{redirect}}}", temp_text)
        # {{RE siehe|Redirect|Something}} -> {{RE siehe|Target|Something}}
        temp_text = re.sub(rf"{{RE siehe\|{redirect_re}\|(.+?)}}", rf"{{RE siehe|{target}|\g<1>}}", temp_text)
        # VORGÄNGER=Redirect -> VORGÄNGER=Target
        temp_text = re.sub(rf"(VORGÄNGER|NACHFOLGER)={redirect_re}\n", rf"\g<1>={target}\n", temp_text)
        return temp_text
