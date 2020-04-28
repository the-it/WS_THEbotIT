from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory, \
    JsonClaimDict


class P31InstanceOf(ClaimFactory):
    """
    Returns the Claim **instance of** -> **(encyclopedic article|cross-reference)**
    """
    ENCYCLOPEDIC_ARTICLE_ITEM = "Q13433827"
    CROSS_REFERENCE_ITEM = "Q1302249"

    def _get_claim_json(self) -> JsonClaimDict:
        if self.re_page[0]["VERWEIS"].value:
            return self.create_claim_json(self.get_property_string(), "wikibase-item", self.CROSS_REFERENCE_ITEM)
        else:
            return self.create_claim_json(self.get_property_string(), "wikibase-item", self.ENCYCLOPEDIC_ARTICLE_ITEM)
