import re
from typing import List, Union

import pywikibot

from service.ws_re.scanner.tasks.base_task import ReScannerTask
from service.ws_re.template.article import Article
from tools.bots.logger import WikiLogger


class RELITask(ReScannerTask):
    """
    Entfernt unerwünschte RE-Verweissyntax für bestimmte Ziel-Lemmata.

    Ersetzungen (pro Ziellemma L):
    - "{{RE siehe|L|Anker}}" -> "Anker"
    - "{{RE siehe|L}}" -> "L"
    - "[[RE:L|Anker]]" -> "Anker"

    Die Ziellemmata werden aus dem Array TARGET_LEMMAS entnommen und iteriert.
    """

    # Diese Liste kann bei Bedarf von außen befüllt/überschrieben werden
    TARGET_LEMMAS: List[str] = [
        # Beispielvorgabe aus Anforderung
        "Leben(a)",
    ]

    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        super().__init__(wiki, logger, debug)
        # Vorab die Regexe je Lemma vorbereiten
        self._compiled_patterns = [self._build_patterns(lemma) for lemma in self.TARGET_LEMMAS]

    @staticmethod
    def _build_patterns(lemma: str):
        """
        Liefert drei (pattern, repl) Tupel für alle geforderten Ersetzungen zu einem Lemma.
        """
        esc = re.escape(lemma)
        # 1) {{RE siehe|Lemma|Anker}} -> Anker
        pat_see_with_anchor = re.compile(rf"\{{\{{RE siehe\|{esc}\|([^}}\|]+)\}}\}}")
        # 2) {{RE siehe|Lemma}} -> Lemma
        pat_see_plain = re.compile(rf"\{{\{{RE siehe\|{esc}\}}\}}")
        # 3) [[RE:Lemma|Anker]] -> Anker
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
        # Über alle Teile der RePage iterieren: Artikel und freie Textsegmente
        for idx, part in enumerate(self.re_page):
            if isinstance(part, Article):
                fixed = self._fix_text_for_all(part.text)
                if fixed != part.text:
                    part.text = fixed
            elif isinstance(part, str):
                fixed = self._fix_text_for_all(part)
                if fixed != part:
                    # String im Seitenarray ersetzen
                    self.re_page[idx] = fixed
        return True
