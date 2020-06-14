from typing import List, Optional

import pywikibot
from pywikibot import ItemPage

from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory
from service.ws_re.scanner.tasks.wikidata.claims._base import SnakParameter
from service.ws_re.scanner.tasks.wikidata.claims._typing import JsonClaimDict


class Neighbour(ClaimFactory):
    @property
    def neighbour(self):
        raise NotImplementedError

    def _get_claim_json(self) -> List[JsonClaimDict]:
        neighbour_item = self._get_item_of_neighbour_lemma()
        if neighbour_item:
            snak_parameter = SnakParameter(property_str=self.get_property_string(),
                                           target_type="wikibase-item",
                                           target=neighbour_item.id)
            return [self.create_claim_json(snak_parameter)]
        return []

    def _get_item_of_neighbour_lemma(self) -> Optional[ItemPage]:
        lemma_neighbour = self._get_lemma_of_neighbour()
        try:
            return lemma_neighbour.data_item()
        except pywikibot.NoPage:
            return None

    def _get_lemma_of_neighbour(self) -> pywikibot.Page:
        lemma_neighbour_str = f"RE:{self.re_page.first_article[self.neighbour].value}"
        lemma_neighbour = pywikibot.Page(self.wikisource, lemma_neighbour_str)
        return lemma_neighbour


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
