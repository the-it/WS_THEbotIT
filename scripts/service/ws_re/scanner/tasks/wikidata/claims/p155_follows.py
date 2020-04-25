from typing import List, Optional

import pywikibot
from pywikibot import ItemPage

from scripts.service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory, \
    JsonClaimDict


def p155(self) -> List[pywikibot.Claim]:
    """

    """


class P155Follows(ClaimFactory):
    """
    Returns the Claim **follows** -> **<Item of predecessor article>**
    """



    def _get_claim_json(self) -> List[JsonClaimDict]:
        predecessor_item = self._get_item_of_predecessor_lemma()
        if predecessor_item:
            return [self.create_claim_json(self.get_property_string(), "wikibase-item", predecessor_item.id)]
        return []

    def _get_item_of_predecessor_lemma(self) -> Optional[ItemPage]:
        lemma_before_this_str = f"RE:{self._first_article['VORGÄNGER'].value}"
        lemma_before_this = pywikibot.Page(self.wikisource, lemma_before_this_str)
        try:
            return lemma_before_this.data_item()
        except pywikibot.NoPage:
            return None
