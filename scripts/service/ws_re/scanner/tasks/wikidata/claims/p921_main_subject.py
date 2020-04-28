from typing import List

import pywikibot

from scripts.service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory, \
    JsonClaimDict, ChangedClaimsDict


class P921MainSubject(ClaimFactory):
    """
    Returns the Claim **main subject** -> **<Item of wikipedia article>**
    """

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
        return [self.create_claim_json(self.get_property_string(), "wikibase-item", wp_data_item.id)]

    def get_claims_to_update(self, data_item: pywikibot.ItemPage) -> ChangedClaimsDict:
        """
        TODO: the diff must handled differently here
        Every claim that is updated can possible add new claims, but can also remove existing claims at the item.
        Which claims is removed or added depends of the specific implementation of the property factory. The standart
        implementation will update all claims as expected by the factory (this include removing possible existing
        claims).

        :param: data_item: item where the specific property is going to be altered

        :returns: A dictionary with claims to add and to remove is returned
        """

        claim_list = [pywikibot.Claim.fromJSON(self.wikidata, claim_json)
                      for claim_json in self._get_claim_json()]
        return self.get_diff_claims_for_replacement(claim_list, data_item)
