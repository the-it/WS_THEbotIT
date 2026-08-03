import re

import pywikibot

from service.ws_re.scanner.tasks.base_task import ReScannerTask
from service.ws_re.template.article import Article
from tools.bots.logger import WikiLogger


class HLTSTask(ReScannerTask):
    """
    Converts hard wiki links to RE articles into the {{RE siehe}} template.

    Replacements:
    - "[[RE:Lemma]]" -> "{{RE siehe|Lemma}}"
    - "[[RE:Lemma|Anchor]]" -> "{{RE siehe|Lemma|Anchor}}"
    """

    _link_regex = re.compile(r"\[\[RE:([^|\]]+)(?:\|([^\]]+))?]]")

    def __init__(self, wiki: pywikibot.site.BaseSite, logger: WikiLogger, debug: bool = True):
        super().__init__(wiki, logger, debug)

    @classmethod
    def _replace(cls, match: re.Match) -> str:
        lemma = match.group(1)
        anchor = match.group(2)
        if anchor:
            return f"{{{{RE siehe|{lemma}|{anchor}}}}}"
        return f"{{{{RE siehe|{lemma}}}}}"

    def _fix_text(self, text: str) -> str:
        return self._link_regex.sub(self._replace, text)

    def task(self) -> bool:
        for idx, part in enumerate(self.re_page):
            if isinstance(part, Article):
                fixed = self._fix_text(part.text)
                if fixed != part.text:
                    part.text = fixed
            elif isinstance(part, str):
                fixed = self._fix_text(part)
                if fixed != part:
                    self.re_page[idx] = fixed
        return True
