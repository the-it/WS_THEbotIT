from typing import List, Optional

import pywikibot
from pywikibot import ItemPage

from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory, \
    JsonClaimDict, SnakParameter


class Neighbour(ClaimFactory):
    @property
    def neighbour(self):
        raise NotImplementedError

    def _get_claim_json(self) -> List[JsonClaimDict]:
        predecessor_item = self._get_item_of_neighbour_lemma()
        if predecessor_item:
            snak_parameter = SnakParameter(property_str=self.get_property_string(),
                                           target_type="wikibase-item",
                                           target=predecessor_item.id)
            return [self.create_claim_json(snak_parameter)]
        return []

    def _get_item_of_neighbour_lemma(self) -> Optional[ItemPage]:
        lemma_neighbour_str = f"RE:{self.re_page.first_article[self.neighbour].value}"
        lemma_neighbour = pywikibot.Page(self.wikisource, lemma_neighbour_str)
        try:
            return lemma_neighbour.data_item()
        except pywikibot.NoPage:
            return None


class P155Follows(Neighbour):
    """
    Returns the Claim **follows** -> **<Item of predecessor article>**
    """
    neighbour = "VORGÄNGER"


class P156FollowedBy(Neighbour):
    """
    Returns the Claim **followed by** -> **<Item of following article>**
    """
    neighbour = "NACHFOLGER"
