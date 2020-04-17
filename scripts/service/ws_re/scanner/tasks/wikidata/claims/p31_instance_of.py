import pywikibot

from scripts.service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory, \
    ChangedClaimsDict
from scripts.service.ws_re.template.re_page import RePage


class P31InstanceOf(ClaimFactory):
    """
    Returns the Claim **instance of** -> **(encyclopedic article|cross-reference)**
    """
    ENCYCLOPEDIC_ARTICLE_ITEM = 13433827
    CROSS_REFERENCE_ITEM = 1302249

    def __init__(self, wikidata: pywikibot.Site):
        super().__init__(wikidata)
        self.CLAIM_DICT = {'mainsnak': {'snaktype': 'value',
                                        'property': self.get_property_string(),
                                        "datatype": "wikibase-item",
                                        "datavalue": {
                                            "value": {
                                                "entity-type": "item",
                                                "numeric-id": self.ENCYCLOPEDIC_ARTICLE_ITEM
                                            },
                                            "type": "wikibase-entityid"
                                        }},
                           'type': 'statement',
                           'rank': 'normal'}

    def get_claims_to_update(self, re_page: RePage, data_item: pywikibot.ItemPage) -> ChangedClaimsDict:
        if re_page[0]["VERWEIS"].value:
            self.CLAIM_DICT["mainsnak"]["datavalue"]["value"]["numeric-id"] = self.CROSS_REFERENCE_ITEM
        else:
            self.CLAIM_DICT["mainsnak"]["datavalue"]["value"]["numeric-id"] = self.ENCYCLOPEDIC_ARTICLE_ITEM
        claim = pywikibot.Claim.fromJSON(self.wikidata, self.CLAIM_DICT)
        old_claims = data_item.claims[self.get_property_string()]
        claims_to_add, claims_to_remove = self._filter_new_vs_old_claim_list([claim], old_claims)
        return self._create_claim_dictionary(claims_to_add, claims_to_remove)
