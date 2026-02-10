from typing import List

import Levenshtein
import pywikibot

from service.ws_re.register.lemma import Lemma
from service.ws_re.scanner.tasks.base_task import ReScannerTask
from tools.bots.logger import WikiLogger


class SKFRTask(ReScannerTask):
    """Task to check sortkeys and suggest better alternatives from redirects."""

    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        super().__init__(wiki, logger, debug)

    def task(self) -> bool:
        """Main task logic."""
        article = self.re_page.first_article

        # Check if sortkey is set
        if article["SORTIERUNG"].value:
            return True

        # Get redirects to this lemma
        redirects = self._get_redirects()
        if not redirects:
            return True

        # Compute sortkey for main lemma
        main_lemma = self.re_page.lemma_without_prefix
        computed_sortkey = Lemma.make_sort_key(main_lemma)

        # Find redirect with smallest Levenshtein distance to computed sortkey
        best_redirect = self._find_best_redirect(redirects, computed_sortkey, main_lemma)

        if best_redirect:
            # Copy sortkey to all articles
            for art in self.re_page.splitted_article_list:
                art["SORTIERUNG"].value = best_redirect
            self.logger.info(
                f"Set SORTIERUNG={best_redirect} for {self.re_page.lemma_without_prefix} "
                f"(applied to {len(self.re_page.splitted_article_list)} article(s))"
            )

        return True

    def _get_redirects(self) -> List[str]:
        """Get list of redirect page titles without 'RE:' prefix."""
        try:
            redirects = []
            for redirect_page in self.re_page.get_redirects():
                redirect_title = redirect_page.title()
                if redirect_title.startswith("RE:"):
                    redirects.append(redirect_title[3:])
            return redirects
        except Exception as error:  # pylint: disable=broad-except
            self.logger.error(f"Error getting redirects for {self.re_page.lemma_as_link}: {error}")
            return []

    def _find_best_redirect(self, redirects: List[str], computed_sortkey: str, main_lemma: str) -> str:
        """
        Find redirect with smallest Levenshtein distance to computed sortkey.

        Returns redirect lemma if it has smaller distance than main lemma, otherwise empty string.
        """
        main_lemma_distance = Levenshtein.distance(main_lemma, computed_sortkey)

        best_redirect = ""
        best_distance = main_lemma_distance

        for redirect in redirects:
            distance = Levenshtein.distance(redirect, computed_sortkey)

            if distance < best_distance:
                best_distance = distance
                best_redirect = redirect

        if best_redirect:
            self.logger.info(
                f"Found better sortkey for {self.re_page.lemma_without_prefix}: "
                f"Using redirect '{best_redirect}' (distance: {best_distance}) "
                f"instead of main lemma (distance: {main_lemma_distance})"
            )

        return best_redirect
