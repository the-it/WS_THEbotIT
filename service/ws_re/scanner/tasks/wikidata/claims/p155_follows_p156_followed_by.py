from typing import List, Optional

import pywikibot

from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory
from service.ws_re.scanner.tasks.wikidata.claims._base import SnakParameter
from service.ws_re.scanner.tasks.wikidata.claims._typing import JsonClaimDict
from service.ws_re.template.article import Article


class Neighbour(ClaimFactory):
    @property
    def neighbour(self):
        raise NotImplementedError

    def _get_claim_json(self) -> List[JsonClaimDict]:
        if snak := self.get_item_of_neighbour_lemma(self.re_page.first_article):
            return [self.create_claim_json(snak)]
        return []

    def get_item_of_neighbour_lemma(self, article: Article) -> Optional[SnakParameter]:
        lemma_neighbour = self._get_lemma_of_neighbour(article)
        try:
            return SnakParameter(property_str=self.get_property_string(),
                                 target_type="wikibase-item",
                                 target=lemma_neighbour.data_item().id)
        except pywikibot.exceptions.NoPageError:
            return None

    def _get_lemma_of_neighbour(self, article: Article) -> pywikibot.Page:
        lemma_neighbour_str = f"RE:{article[self.neighbour].value}"
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
