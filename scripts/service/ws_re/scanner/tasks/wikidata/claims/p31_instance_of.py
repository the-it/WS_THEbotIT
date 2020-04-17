import pywikibot

from scripts.service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory, \
    ChangedClaimsDict
from scripts.service.ws_re.template.re_page import RePage


class P31InstanceOf(ClaimFactory):
    """
    Returns the Claim **instance of** -> **(encyclopedic article|cross-reference)**
    """
    ENCYCLOPEDIC_ARTICLE_ITEM = "Q13433827"
    CROSS_REFERENCE_ITEM = "Q1302249"

    def get_claims_to_update(self, re_page: RePage, data_item: pywikibot.ItemPage) -> ChangedClaimsDict:
        claim = pywikibot.Claim(self.wikidata, self.get_property_string())
        if re_page[0]["VERWEIS"].value:
            target = pywikibot.ItemPage(self.wikidata, self.CROSS_REFERENCE_ITEM)
        else:
            target = pywikibot.ItemPage(self.wikidata, self.ENCYCLOPEDIC_ARTICLE_ITEM)
        claim.setTarget(target)
        old_claims = data_item.claims[self.get_property_string()]
        claims_to_add, claims_to_remove = self._filter_new_vs_old_claim_list([claim], old_claims)
        return self._create_claim_dictionary(claims_to_add, claims_to_remove)
