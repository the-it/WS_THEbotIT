from typing import List

from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory
from service.ws_re.scanner.tasks.wikidata.claims._base import SnakParameter
from service.ws_re.scanner.tasks.wikidata.claims._typing import JsonClaimDict
from service.ws_re.scanner.tasks.wikidata.base import get_article_type


class P31InstanceOf(ClaimFactory):
    """
    Returns the Claim **instance of** -> **(encyclopedic article|cross-reference)**
    """
    ENCYCLOPEDIC_ARTICLE_ITEM = "Q13433827"
    CROSS_REFERENCE_ITEM = "Q1302249"
    INDEX = "Q873506"
    PROLOGUE = "Q920285"

    def _get_claim_json(self) -> List[JsonClaimDict]:
        article_type = get_article_type(self.re_page)
        if article_type == "index":
            target = self.INDEX
        elif article_type == "prologue":
            target = self.PROLOGUE
        elif article_type == "crossref":
            target = self.CROSS_REFERENCE_ITEM
        else:
            target = self.ENCYCLOPEDIC_ARTICLE_ITEM
        snak_parameter = SnakParameter(property_str=self.get_property_string(),
                                       target_type="wikibase-item",
                                       target=target)
        return [self.create_claim_json(snak_parameter)]
