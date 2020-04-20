from typing import List, Dict

import pywikibot

from scripts.service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory, \
    ChangedClaimsDict
from scripts.service.ws_re.template.re_page import RePage


class P50Author(ClaimFactory):
    """
    Returns the Claim **author** -> **<Item of author of RE lemma>**
    """

    def _get_claim_json(self, re_page: RePage) -> List[ChangedClaimsDict]:
        pass

    def get_claims_to_update(self, re_page: RePage, data_item: pywikibot.ItemPage) -> ChangedClaimsDict:
        claim_list  = [pywikibot.Claim.fromJSON(self.wikidata, claim_json)
                       for claim_json in self._get_claim_json(re_page)]
        return self.get_diff_claims_for_replacement(claim_list, data_item)

    def _get_author_list(self) -> List[str]:
        author_items: List[str] = []
        for author in self._authors_of_first_article:
            author_lemma = pywikibot.Page(self.wikisource, author.name)
            if not author_lemma.exists():
                continue
            try:
                # append the item of the author, if it exists
                author_items.append(author_lemma.data_item().id)
            except pywikibot.NoPage:
                continue
        return author_items
