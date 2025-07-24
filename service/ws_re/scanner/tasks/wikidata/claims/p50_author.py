from typing import List

import pywikibot

from service.ws_re.scanner.tasks.wikidata.claims._base import SnakParameter
from service.ws_re.scanner.tasks.wikidata.claims._typing import JsonClaimDict
from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory
from service.ws_re.template.article import Article


class P50Author(ClaimFactory):
    """
    Returns the Claim **author** -> **<Item of author of RE lemma>**
    """

    def _get_claim_json(self) -> List[JsonClaimDict]:
        return [self.create_claim_json(snak) for snak in self._get_author_list(self.re_page.splitted_article_list[0])]

    def _get_author_list(self, articles: list[Article]) -> List[SnakParameter]:
        author_items: List[str] = []
        for author in self.get_authors_article(articles):
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
        return [SnakParameter(property_str=self.get_property_string(),
                              target_type="wikibase-item",
                              target=author_id)
                for author_id in author_items]
