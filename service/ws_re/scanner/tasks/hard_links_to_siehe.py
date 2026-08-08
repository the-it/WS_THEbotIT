import re

import pywikibot

from service.ws_re.register.registers import Registers
from service.ws_re.scanner.tasks.base_task import ReScannerTask
from service.ws_re.template.article import Article
from tools.bots.logger import WikiLogger


class HLTSTask(ReScannerTask):
    """
    Converts hard wiki links to RE articles into the {{RE siehe}} template.

    Only links whose target is NOT a lemma of the local register data are converted, the template
    handles those gracefully. Links to known lemmas are kept as they are. Links with a section
    anchor ("[[RE:Lemma#Abschnitt]]") are never converted, the template can't express them.

    Replacements:
    - "[[RE:Lemma]]" -> "{{RE siehe|Lemma}}"
    - "[[RE:Lemma|Anchor]]" -> "{{RE siehe|Lemma|Anchor}}"
    """

    _link_regex = re.compile(r"\[\[RE:([^|\]]+)(?:\|([^\]]+))?]]")

    def __init__(self, wiki: pywikibot.site.BaseSite, logger: WikiLogger, debug: bool = True):
        super().__init__(wiki, logger, debug)
        self._lemma_names: set[str] | None = None
        self._unknown_targets: set[tuple[str, str]] = set()

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
        anchor = match.group(2)
        if "#" in target:
            return match.group(0)
        if self._resolve_lemma(target):
            # lemma is known in the register, the hard link stays as it is
            return match.group(0)
        self._unknown_targets.add((target, self.re_page.lemma_without_prefix))
        if anchor:
            return f"{{{{RE siehe|{target}|{anchor}}}}}"
        return f"{{{{RE siehe|{target}}}}}"

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

    def finish_task(self):
        if self._unknown_targets:
            entries = [
                f"[[RE:{target}]] verlinkt von [[RE:{source}]]" for target, source in sorted(self._unknown_targets)
            ]
            self.logger.info(f"Links converted, lemma unknown in register: {entries}")
        super().finish_task()
