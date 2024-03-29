from typing import List

import pywikibot

from service.ws_re.scanner.tasks.wikidata.claims._base import SnakParameter
from service.ws_re.scanner.tasks.wikidata.claims._typing import ChangedClaimsDict, JsonClaimDict
from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory


class P921MainSubject(ClaimFactory):
    """
    Returns the Claim **main subject** -> **<Item of wikipedia article>**
    """

    ERROR_CAT = "RE:Wartung Wikidata (WD!=WS)"

    def _get_claim_json(self) -> List[JsonClaimDict]:
        wp_article = str(self.re_page.first_article["WIKIPEDIA"].value)
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
        except (pywikibot.exceptions.NoPageError, pywikibot.exceptions.InvalidTitleError):
            return []
        # finally create the claim
        snak = SnakParameter(property_str=self.get_property_string(),
                             target_type="wikibase-item",
                             target=wp_data_item.id)

        return [self.create_claim_json(snak, references=[[self._IMPORTED_FROM_WIKISOURCE]])]

    def get_claims_to_update(self, data_item: pywikibot.ItemPage) -> ChangedClaimsDict:
        """
        Only add claims, if no claim already exist.
        Alert with an error if existing claim and added claim are different.

        :param: data_item: item where the specific property is going to be altered

        :returns: A dictionary with claims to add and to remove is returned
        """
        claim_json = self._get_claim_json()
        if not claim_json:
            return self._create_claim_dictionary([], [])
        new_claim: pywikibot.Claim = pywikibot.Claim.fromJSON(self.wikidata, claim_json[0])
        old_claims = self.get_old_claims(data_item)
        if not old_claims:
            return self._create_claim_dictionary([new_claim], [])
        if not new_claim.same_as(old_claims[0]):
            self.re_page.add_error_category(self.ERROR_CAT)
        else:
            self.re_page.remove_error_category(self.ERROR_CAT)
        return self._create_claim_dictionary([], [])
