import re
from typing import List

import pywikibot

from service.ws_re.scanner.tasks.base_task import ReScannerTask
from service.ws_re.template.article import Article
from tools.bots.logger import WikiLogger


class RELITask(ReScannerTask):
    """
    Removes unwanted RE cross-reference syntax for specific target lemmas.

    Replacements (per target lemma L):
    - "{{RE siehe|L|Anchor}}" -> "Anchor"
    - "{{RE siehe|L}}" -> "L"
    - "[[RE:L|Anchor]]" -> "Anchor"

    The target lemmas are taken from the TARGET_LEMMAS array and iterated over.
    """

    # This list can be populated/overwritten from outside if needed
    TARGET_LEMMAS: List[str] = [
        "Λεβήν",
        "Leben(a)",
    ]

    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        super().__init__(wiki, logger, debug)
        # Pre-compile the regex patterns for each lemma
        self._compiled_patterns = [self._build_patterns(lemma) for lemma in self.TARGET_LEMMAS]

    @staticmethod
    def _build_patterns(lemma: str):
        """
        Returns three (pattern, repl) tuples for all required replacements for a lemma.
        """
        esc = re.escape(lemma)
        # 1) {{RE siehe|Lemma|Anchor}} -> Anchor
        pat_see_with_anchor = re.compile(rf"\{{\{{RE siehe\|{esc}\|([^}}\|]+)\}}\}}")
        # 2) {{RE siehe|Lemma}} -> Lemma
        pat_see_plain = re.compile(rf"\{{\{{RE siehe\|{esc}\}}\}}")
        # 3) [[RE:Lemma|Anchor]] -> Anchor
        pat_link_with_anchor = re.compile(rf"\[\[RE:{esc}\|([^\]|]+)\]\]")

        return (
            (pat_see_with_anchor, r"\1"),
            (pat_see_plain, lemma),
            (pat_link_with_anchor, r"\1"),
        )

    def _fix_text_for_all(self, text: str) -> str:
        new_text = text
        for pattern_group in self._compiled_patterns:
            for pat, repl in pattern_group:
                new_text = pat.sub(repl, new_text)
        return new_text

    def task(self) -> bool:
        # Iterate over all parts of the RePage: Article objects and plain text segments
        for idx, part in enumerate(self.re_page):
            if isinstance(part, Article):
                fixed = self._fix_text_for_all(part.text)
                if fixed != part.text:
                    part.text = fixed
            elif isinstance(part, str):
                fixed = self._fix_text_for_all(part)
                if fixed != part:
                    # Replace the string in the page's list
                    self.re_page[idx] = fixed
        return True
