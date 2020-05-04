from typing import List

from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory, \
    JsonClaimDict, SnakParameter


class P31InstanceOf(ClaimFactory):
    """
    Returns the Claim **instance of** -> **(encyclopedic article|cross-reference)**
    """
    ENCYCLOPEDIC_ARTICLE_ITEM = "Q13433827"
    CROSS_REFERENCE_ITEM = "Q1302249"

    def _get_claim_json(self) -> List[JsonClaimDict]:
        if self.re_page[0]["VERWEIS"].value:
            snak_parameter = SnakParameter(property_str=self.get_property_string(),
                                           target_type="wikibase-item",
                                           target=self.CROSS_REFERENCE_ITEM)
        else:
            snak_parameter = SnakParameter(property_str=self.get_property_string(),
                                           target_type="wikibase-item",
                                           target=self.ENCYCLOPEDIC_ARTICLE_ITEM)
        return [self.create_claim_json(snak_parameter)]
