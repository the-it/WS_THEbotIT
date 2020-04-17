from typing import List

import pywikibot

from scripts.service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory, \
    ChangedClaimsDict
from scripts.service.ws_re.template.re_page import RePage


def p50(self) -> List[pywikibot.Claim]:
    """

    """
    author_items = self._p50_get_author_list()
    claim_list: List[pywikibot.Claim] = []
    for author in author_items:
        claim = pywikibot.Claim(self.wikidata, 'P50')
        claim.setTarget(author)
        claim_list.append(claim)
    return claim_list

    def _p50_get_author_list(self) -> List[pywikibot.Claim]:
        author_items: List[pywikibot.Claim] = []
        for author in self._authors_of_first_article:
            author_lemma = pywikibot.Page(self.wiki, author.name)
            if not author_lemma.exists():
                continue
            try:
                # append the item of the author, if it exists
                author_items.append(author_lemma.data_item())
            except pywikibot.NoPage:
                continue
        return author_items


class P50Author(ClaimFactory):
    """
    Returns the Claim **author** -> **<Item of author of RE lemma>**
    """
    def _get_claim_json(self, re_page: RePage):
        if re_page[0]["VERWEIS"].value:
            return self.create_claim_json(self.get_property_string(), "wikibase-item", self.CROSS_REFERENCE_ITEM)
        else:
            return self.create_claim_json(self.get_property_string(), "wikibase-item", self.ENCYCLOPEDIC_ARTICLE_ITEM)

    def get_claims_to_update(self, re_page: RePage, data_item: pywikibot.ItemPage) -> ChangedClaimsDict:
        claim = pywikibot.Claim.fromJSON(self.wikidata, self._get_claim_json(re_page))
        return self.get_diff_claims_for_replacement([claim], data_item)
