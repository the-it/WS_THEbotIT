import re
import time

import pywikibot

from service.ws_re.scanner.tasks.base_task import ReScannerTask
from tools import save_if_changed
from tools.bots.logger import WikiLogger

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
            r"Wikisource:|"
            r"RE:Wartung:"
            r").*"
        )

    def task(self) -> bool:
        self.iterate_through_redirects(repair=True)
        self.iterate_through_redirects(report=True)
        return True

    def iterate_through_redirects(self, repair: bool = False, report: bool = False):
        redirects = self.collect_redirect_chain()
        # every title in the chain resolves to the same target, so a backlink may
        # reference an intermediate redirect rather than the one being iterated
        redirect_titles = [redirect.title()[3:] for redirect in redirects]
        for redirect in redirects:
            filtered_list = self.filter_link_list(self.get_backlinks(redirect))
            if filtered_list:
                if repair:
                    self.rename_redirects_to_target(filtered_list, redirect_titles)
                    time.sleep(2)
                if report:
                    self.re_page.add_error_category(self.error_category)
                    return
        self.re_page.remove_error_category(self.error_category)

    def collect_redirect_chain(self) -> list[pywikibot.Page]:
        """Transitive closure of redirects pointing at the RE page.

        ``get_redirects()`` (the MediaWiki ``prop=redirects`` API) only returns
        *direct* redirects. Walk the graph upward so that chains
        ``A -> B -> RE:Target`` also yield ``A``. Cycle-safe via ``seen``.
        """
        seen: set[str] = set()
        chain: list[pywikibot.Page] = []
        queue: list[pywikibot.Page] = self.re_page.get_redirects()
        while queue:
            redirect = queue.pop(0)
            title = redirect.title()
            if title in seen:
                continue
            seen.add(title)
            chain.append(redirect)
            queue.extend(redirect.redirects())  # next hop up the chain
        return chain

    def rename_redirects_to_target(self, filtered_list: list[str], redirect_titles: list[str]):
        for entry in filtered_list:
            page = pywikibot.Page(self.wiki, entry)
            new_text = self.replace_redirect_links(page.text, redirect_titles, self.re_page.lemma_without_prefix)
            save_if_changed(page, new_text, f"Link korrigiert zu {self.re_page.page}")

    @staticmethod
    def get_backlinks(redirect_page: pywikibot.Page) -> list[str]:
        return [page.title() for page in redirect_page.backlinks()]

    def filter_link_list(self, link_list: list[str]) -> list[str]:
        return [link for link in link_list if self.filter_regex.search(link) is None]

    @staticmethod
    def replace_redirect_links(text: str, redirects: list[str], target: str):
        # any title in the redirect chain resolves to the target; match all of them
        # at once, longest first so the alternation prefers the most specific title
        escaped = sorted((redirect.translate(REGEX_TRANSLATION) for redirect in redirects),
                         key=len, reverse=True)
        redirect_re = "|".join(escaped)
        # [[RE:Redirect(#part)(|Something)]] -> [[RE:Target(#part)(|Something)]]
        temp_text = re.sub(rf"\[\[RE:(?:{redirect_re})(#|\||\]\])", rf"[[RE:{target}\g<1>", text)
        # {{RE siehe|Redirect}} -> {{RE siehe|Target|Redirect}}
        temp_text = re.sub(rf"{{RE siehe\|({redirect_re})}}", rf"{{RE siehe|{target}|\g<1>}}", temp_text)
        # {{RE siehe|Redirect|Something}} -> {{RE siehe|Target|Something}}
        temp_text = re.sub(rf"{{RE siehe\|(?:{redirect_re})\|(.+?)}}", rf"{{RE siehe|{target}|\g<1>}}", temp_text)
        # VORGÄNGER=Redirect -> VORGÄNGER=Target
        temp_text = re.sub(rf"(VORGÄNGER|NACHFOLGER)=(?:{redirect_re})\n", rf"\g<1>={target}\n", temp_text)
        return temp_text
