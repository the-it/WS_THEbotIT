import re

import pywikibot

from service.ws_re.register.authors import Authors
from service.ws_re.scanner.tasks.base_task import ReScannerTask
from service.ws_re.template.article import Article
from tools.bots.pi import WikiLogger


class KSCHTask(ReScannerTask):
    # for next check   https://petscan.wmflabs.org/?edits%5Banons%5D=both&project=wikisource
    # &categories=Paulys%20Realencyclop%C3%A4die%20der%20classischen%20Altertumswissenschaft&language=de&sortby=size
    # &edits%5Bflagged%5D=both&cb_labels_any_l=1&cb_labels_yes_l=1&edits%5Bbots%5D=both
    # &templates_yes=RE%20keine%20Sch%C3%B6pfungsh%C3%B6he&cb_labels_no_l=1&interface_language=en
    # &search_max_results=500&active_tab=tab_pageprops&doit=

    _regex_template = re.compile(r"{{RE[_ ]keine[_ ]Schöpfungshöhe(?:\|(\d\d\d\d))?}}")

    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        super().__init__(wiki, logger, debug)
        self.authors = Authors()

    def task(self):
        for re_article in self.re_page:
            if isinstance(re_article, Article):
                template_match = self._regex_template.search(re_article.text)
                if template_match:
                    if template_match.group(1):
                        self._replace_template(re_article, template_match.group(1))
                    # no year provided
                    else:
                        self._handle_without_provided_year(re_article)

    def _handle_without_provided_year(self, re_article):
        authors = self.authors.get_author_by_mapping(re_article.author[0], re_article["BAND"].value)
        if len(authors) != 1:
            return
        author = authors[0]
        if author.death:
            self._replace_template(re_article, str(author.death))
        else:
            if author.birth:
                self._replace_template(re_article, str(author.birth))

    def _replace_template(self, re_article: Article, year: str):
        re_article["TODESJAHR"].value = year
        re_article["KEINE_SCHÖPFUNGSHÖHE"].value = True
        re_article.text = self._regex_template.sub("", re_article.text).strip()
