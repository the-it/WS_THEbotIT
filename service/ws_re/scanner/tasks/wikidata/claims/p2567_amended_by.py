from typing import List

from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory
from service.ws_re.scanner.tasks.wikidata.claims._base import SnakParameter
from service.ws_re.scanner.tasks.wikidata.claims._typing import JsonClaimDict
from service.ws_re.scanner.tasks.wikidata.claims.p1433_published_in import P1433PublishedIn
from service.ws_re.scanner.tasks.wikidata.claims.p155_follows_p156_followed_by import P155Follows, P156FollowedBy
from service.ws_re.scanner.tasks.wikidata.claims.p3903_column import P3903Column
from service.ws_re.scanner.tasks.wikidata.claims.p50_author import P50Author
from service.ws_re.scanner.tasks.wikidata.claims.p577_publication_date import P577PublicationDate


class P2567AmendedBy(ClaimFactory):
    """
    Returns the Claim **amended by** -> **issue of the amendment** + some qualifiers
    """

    ITEM_R = "Q26470176"

    def __init__(self, re_page, logger):
        super().__init__(re_page, logger)
        self.p1433_published_in = P1433PublishedIn(re_page, self.logger)
        self.p50_author = P50Author(re_page, logger)
        self.p577_publication_date = P577PublicationDate(re_page, logger)
        self.p3903_column = P3903Column(re_page, logger)
        self.p155_follows = P155Follows(re_page, logger)
        self.p156_followed_by = P156FollowedBy(re_page, logger)

    def _get_claim_json(self) -> List[JsonClaimDict]:
        claim_list: list[JsonClaimDict] = []
        for idx, article_list in enumerate(self.re_page.splitted_article_list):
            # skip first entry, this isn't an amendment
            if idx == 0:
                continue
            published_in_snak = self.p1433_published_in.get_volume_snak(article_list[0])
            published_in_snak.property_str = self.get_property_string()
            if published_in_snak.target == self.ITEM_R:
                continue
            qualifiers: List[SnakParameter] = []
            qualifiers += self.p50_author.get_author_list(article_list)
            qualifiers.append(self.p577_publication_date.get_snack(article_list[0]))
            qualifiers.append(self.p3903_column.get_column_snak(article_list[0]))
            if follows := self.p155_follows.get_item_of_neighbour_lemma(article_list[0]):
                qualifiers.append(follows)
            if followed_by := self.p156_followed_by.get_item_of_neighbour_lemma(article_list[0]):
                qualifiers.append(followed_by)
            claim_list.append(self.create_claim_json(published_in_snak, qualifiers=qualifiers))
        return claim_list
