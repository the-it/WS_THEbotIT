from typing import List

import pywikibot

from service.ws_re.scanner.tasks.wikidata.claims._base import SnakParameter
from service.ws_re.scanner.tasks.wikidata.claims._typing import JsonClaimDict
from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory


class P50Author(ClaimFactory):
    """
    Returns the Claim **author** -> **<Item of author of RE lemma>**
    """

    def _get_claim_json(self) -> List[JsonClaimDict]:
        return [self.create_claim_json(SnakParameter(property_str=self.get_property_string(),
                                                     target_type="wikibase-item",
                                                     target=id))
                for id in self._get_author_list()]

    def _get_author_list(self) -> List[str]:
        author_items: List[str] = []
        for author in self._authors_of_first_article:
            author_lemma = None
            if author.ws_lemma:
                author_lemma = pywikibot.Page(self.wikisource, author.ws_lemma)
            elif author.wp_lemma:
                author_lemma = pywikibot.Page(self.wikipedia, author.wp_lemma)
            if author_lemma:
                try:
                    # append the item of the author, if it exists and is not already in the list
                    if (author_wikidata_id := author_lemma.data_item().id) not in author_items:
                        author_items.append(author_wikidata_id)
                except pywikibot.exceptions.NoPageError:
                    continue
        return author_items
