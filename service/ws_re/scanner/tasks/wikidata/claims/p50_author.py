from typing import List

import pywikibot

from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory, \
    JsonClaimDict


class P50Author(ClaimFactory):
    """
    Returns the Claim **author** -> **<Item of author of RE lemma>**
    """

    def _get_claim_json(self) -> List[JsonClaimDict]:
        return [self.create_claim_json(self.get_property_string(), "wikibase-item", id)
                for id in self._get_author_list()]

    def _get_author_list(self) -> List[str]:
        author_items: List[str] = []
        for author in self._authors_of_first_article():
            author_lemma = pywikibot.Page(self.wikisource, author.name)
            try:
                # append the item of the author, if it exists
                author_items.append(author_lemma.data_item().id)
            except pywikibot.NoPage:
                continue
        return author_items


