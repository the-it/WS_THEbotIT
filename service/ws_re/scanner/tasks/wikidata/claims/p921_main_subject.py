from typing import List

import pywikibot

from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory, \
    JsonClaimDict, ChangedClaimsDict, SnakParameter


class P921MainSubject(ClaimFactory):
    """
    Returns the Claim **main subject** -> **<Item of wikipedia article>**
    """
    IMPORTED_FROM_WIKIMEDIA_PROJECT = "P143"
    GERMAN_WIKISOURCE = "Q15522295"

    def _get_claim_json(self) -> List[JsonClaimDict]:
        wp_article = str(self._first_article["WIKIPEDIA"].value)
        # if no wp_article is present, there is nothing to connect
        if not wp_article:
            return []
        # handle the case of an implicit de:
        if ":" not in wp_article:
            wp_article = f"de:{wp_article}"
        language, wp_page_str = wp_article.split(":")
        wp_site: pywikibot.Site = pywikibot.Site(code=language, fam="wikipedia")
        wp_page: pywikibot.Page = pywikibot.Page(wp_site, wp_page_str)
        # try to fetch the data item of the page, if not there is nothing to connect
        try:
            wp_data_item: pywikibot.ItemPage = wp_page.data_item()
        except pywikibot.NoPage:
            return []
        # finally create the claim
        snak = SnakParameter(property_str=self.get_property_string(),
                             target_type="wikibase-item",
                             target=wp_data_item.id)
        ref_snak = SnakParameter(property_str=self.IMPORTED_FROM_WIKIMEDIA_PROJECT,
                             target_type="wikibase-item",
                             target=self.GERMAN_WIKISOURCE)
        return [self.create_claim_json(snak, references=[[ref_snak]])]

    def get_claims_to_update(self, data_item: pywikibot.ItemPage) -> ChangedClaimsDict:
        """
        Every claim that is updated can possible add new claims, but can also remove existing claims at the item.
        Which claims is removed or added depends of the specific implementation of the property factory. The standart
        implementation will update all claims as expected by the factory (this include removing possible existing
        claims).

        :param: data_item: item where the specific property is going to be altered

        :returns: A dictionary with claims to add and to remove is returned
        """
        claim_json = self._get_claim_json()
        if not claim_json:
            return self._create_claim_dictionary([], [])
        new_claim: pywikibot.Claim = pywikibot.Claim.fromJSON(self.wikisource, claim_json[0])
        old_claims = data_item.claims[self.get_property_string()]
        if not old_claims:
            return self._create_claim_dictionary([new_claim], [])
        if not new_claim.same_as(old_claims[0]):
            self.re_page.add_error_category("RE:Wartung Wikidata (WD!=WS)")
        return self._create_claim_dictionary([], [])
