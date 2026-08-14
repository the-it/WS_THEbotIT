import re

import pywikibot

from service.ws_re.register.registers import Registers
from service.ws_re.scanner.tasks.base_task import ReScannerTask
from service.ws_re.template.article import Article
from tools.bots.logger import WikiLogger


class HLTSTask(ReScannerTask):
    """
    Converts hard wiki links to RE articles into the {{RE siehe}} template, and vice versa.

    A hard link whose target is NOT a lemma of the local register data is converted to
    {{RE siehe}}, the template handles missing lemmas gracefully. A hard link to a known lemma is
    kept as it is. Links with a section anchor ("[[RE:Lemma#Abschnitt]]") are never converted, the
    template can't express them.

    Conversely, a {{RE siehe}} template whose target IS a lemma of the local register data is
    converted to a hard link, since the target article actually exists.

    Replacements:
    - "[[RE:Lemma]]" -> "{{RE siehe|Lemma}}" (Lemma unknown in register)
    - "[[RE:Lemma|Anzeigetext]]" -> "{{RE siehe|Lemma|Anzeigetext}}" (Lemma unknown in register)
    - "[[RE:Lemma]]" -> "[[RE:Lemma|Lemma]]" (Lemma known in register)
    - "{{RE siehe|Lemma}}" -> "[[RE:Lemma|Lemma]]" (Lemma known in register)
    - "{{RE siehe|Lemma|Anzeigetext}}" -> "[[RE:Lemma|Anzeigetext]]" (Lemma known in register)

    While this task is still being rolled out carefully, it only changes MAX_CHANGED_ARTICLES
    articles per scanner run (the scanner runs once a night), then leaves the rest untouched
    until the next run.
    """

    _link_regex = re.compile(r"\[\[RE:([^|\]]+)(?:\|([^\]]+))?]]")
    _siehe_regex = re.compile(r"\{\{RE siehe\|([^|{}]+)(?:\|([^{}]+))?}}")
    MAX_CHANGED_ARTICLES = 10

    def __init__(self, wiki: pywikibot.site.BaseSite, logger: WikiLogger, debug: bool = True):
        super().__init__(wiki, logger, debug)
        self._lemma_names: set[str] | None = None
        self._unknown_targets: set[tuple[str, str]] = set()
        self._changed_articles = 0

    @property
    def lemma_names(self) -> set[str]:
        """All lemma names of the local register data, lazily loaded on first use."""
        if self._lemma_names is None:
            self._lemma_names = {lemma.lemma for register in Registers().volumes.values() for lemma in register.lemmas}
        return self._lemma_names

    def _resolve_lemma(self, target: str) -> str | None:
        """Return the register lemma a link target points to, None if there is none."""
        normalized = target.replace("_", " ").strip()
        if normalized in self.lemma_names:
            return normalized
        # MediaWiki capitalizes the first character of a page title
        if normalized:
            capitalized = normalized[0].upper() + normalized[1:]
            if capitalized in self.lemma_names:
                return capitalized
        return None

    def _replace(self, match: re.Match) -> str:
        target = match.group(1)
        display_text = match.group(2)
        if "#" in target:
            return match.group(0)
        if self._resolve_lemma(target):
            # lemma is known in the register, keep the hard link but hide the "RE:" prefix
            return f"[[RE:{target}|{display_text or target}]]"
        self._unknown_targets.add((target, self.re_page.lemma_without_prefix))
        if display_text:
            return f"{{{{RE siehe|{target}|{display_text}}}}}"
        return f"{{{{RE siehe|{target}}}}}"

    def _replace_siehe(self, match: re.Match) -> str:
        target = match.group(1)
        display_text = match.group(2)
        if not self._resolve_lemma(target):
            # lemma is unknown in the register, the template stays as it is
            return match.group(0)
        # keep the "RE:" prefix out of the rendered text
        return f"[[RE:{target}|{display_text or target}]]"

    def _fix_text(self, text: str) -> str:
        text = self._link_regex.sub(self._replace, text)
        return self._siehe_regex.sub(self._replace_siehe, text)

    def task(self) -> bool:
        if self._changed_articles >= self.MAX_CHANGED_ARTICLES:
            return True
        page_changed = False
        for idx, part in enumerate(self.re_page):
            if isinstance(part, Article):
                fixed = self._fix_text(part.text)
                if fixed != part.text:
                    part.text = fixed
                    page_changed = True
            elif isinstance(part, str):
                fixed = self._fix_text(part)
                if fixed != part:
                    self.re_page[idx] = fixed
                    page_changed = True
        if page_changed:
            self._changed_articles += 1
        return True

    def finish_task(self):
        if self._unknown_targets:
            entries = [
                f"[[RE:{target}]] verlinkt von [[RE:{source}]]" for target, source in sorted(self._unknown_targets)
            ]
            self.logger.info(f"Links converted, lemma unknown in register: {entries}")
        super().finish_task()
