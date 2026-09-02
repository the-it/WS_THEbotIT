import re

import pywikibot

from service.ws_re.register.registers import Registers
from service.ws_re.scanner.tasks.base_task import ReScannerTask
from service.ws_re.template.article import Article
from tools.bots.logger import WikiLogger


class HLTSTask(ReScannerTask):
    """
    Converts hard wiki links to RE articles into the {{RE siehe}} template, and vice versa.

    A hard link whose target lemma's article doesn't actually exist (Lemma.exists, i.e.
    proof_read is set) is converted to {{RE siehe}}, the template handles missing lemmas
    gracefully. A hard link to an existing lemma is kept as it is. Links with a section anchor
    ("[[RE:Lemma#Abschnitt]]") are never converted, the template can't express them.

    Conversely, a {{RE siehe}} template whose target lemma's article exists is converted to a
    hard link. The target must match the register lemma name exactly, including case (page
    titles on de.wikisource are case-sensitive even in their first character); a mismatch is
    left as {{RE siehe}} rather than risking a link to the wrong, differently-cased page.

    Replacements:
    - "[[RE:Lemma]]" -> "{{RE siehe|Lemma}}" (Lemma's article doesn't exist)
    - "[[RE:Lemma|Anzeigetext]]" -> "{{RE siehe|Lemma|Anzeigetext}}" (Lemma's article doesn't exist)
    - "[[RE:Lemma]]" -> "[[RE:Lemma|Lemma]]" (Lemma's article exists)
    - "{{RE siehe|Lemma}}" -> "[[RE:Lemma|Lemma]]" (Lemma's article exists)
    - "{{RE siehe|Lemma|Anzeigetext}}" -> "[[RE:Lemma|Anzeigetext]]" (Lemma's article exists)

    While this task is still being rolled out carefully, it only changes MAX_CHANGED_ARTICLES
    articles per scanner run (the scanner runs once a night), then leaves the rest untouched
    until the next run.
    """

    _link_regex = re.compile(r"\[\[RE:([^|\]]+)(?:\|([^\]]+))?]]")
    _siehe_regex = re.compile(r"\{\{RE siehe\|([^|{}]+)(?:\|([^{}]+))?}}")

    def __init__(self, wiki: pywikibot.site.BaseSite, logger: WikiLogger, debug: bool = True):
        super().__init__(wiki, logger, debug)
        self._existing_lemma_names: set[str] | None = None
        self._unknown_targets: set[tuple[str, str]] = set()

    @property
    def existing_lemma_names(self) -> set[str]:
        """Lemma names of the local register data whose article page actually exists."""
        if self._existing_lemma_names is None:
            self._existing_lemma_names = {
                lemma.lemma for register in Registers().volumes.values() for lemma in register.lemmas if lemma.exists
            }
        return self._existing_lemma_names

    def _resolve_lemma(self, target: str) -> str | None:
        """Return the existing register lemma a link target points to, None if there is none.
        """
        normalized = target.replace("_", " ").strip()
        if normalized in self.existing_lemma_names:
            return normalized
        return None

    def _replace(self, match: re.Match) -> str:
        target = match.group(1)
        display_text = match.group(2)
        if "#" in target:
            return match.group(0)
        if self._resolve_lemma(target):
            # lemma's article exists, keep the hard link but hide the "RE:" prefix
            return f"[[RE:{target}|{display_text or target}]]"
        self._unknown_targets.add((target, self.re_page.lemma_without_prefix))
        if display_text:
            return f"{{{{RE siehe|{target}|{display_text}}}}}"
        return f"{{{{RE siehe|{target}}}}}"

    def _replace_siehe(self, match: re.Match) -> str:
        target = match.group(1)
        display_text = match.group(2)
        resolved = self._resolve_lemma(target)
        if not resolved:
            # lemma doesn't exactly match an existing register lemma, stays as it is
            return match.group(0)
        return f"[[RE:{resolved}|{display_text or target}]]"

    def _fix_text(self, text: str) -> str:
        text = self._link_regex.sub(self._replace, text)
        return self._siehe_regex.sub(self._replace_siehe, text)

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

    def finish_task(self):
        if self._unknown_targets:
            entries = [
                f"[[RE:{target}]] verlinkt von [[RE:{source}]]" for target, source in sorted(self._unknown_targets)
            ]
            self.logger.info(f"Links converted, lemma's article doesn't exist: {entries}")
        super().finish_task()
