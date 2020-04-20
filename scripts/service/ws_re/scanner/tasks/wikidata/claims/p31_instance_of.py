from typing import List

import pywikibot

from scripts.service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory, \
    ChangedClaimsDict, JsonClaimDict
from scripts.service.ws_re.template.re_page import RePage


class P31InstanceOf(ClaimFactory):
    """
    Returns the Claim **instance of** -> **(encyclopedic article|cross-reference)**
    """
    ENCYCLOPEDIC_ARTICLE_ITEM = "Q13433827"
    CROSS_REFERENCE_ITEM = "Q1302249"

    def _get_claim_json(self, re_page: RePage) -> JsonClaimDict:
        if re_page[0]["VERWEIS"].value:
            return self.create_claim_json(self.get_property_string(), "wikibase-item", self.CROSS_REFERENCE_ITEM)
        else:
            return self.create_claim_json(self.get_property_string(), "wikibase-item", self.ENCYCLOPEDIC_ARTICLE_ITEM)

    def get_claims_to_update(self, re_page: RePage, data_item: pywikibot.ItemPage) -> ChangedClaimsDict:
        claim = pywikibot.Claim.fromJSON(self.wikidata, self._get_claim_json(re_page))
        return self.get_diff_claims_for_replacement([claim], data_item)
