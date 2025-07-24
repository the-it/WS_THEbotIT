from typing import List

from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory
from service.ws_re.scanner.tasks.wikidata.claims._base import SnakParameter
from service.ws_re.scanner.tasks.wikidata.claims._typing import JsonClaimDict
from service.ws_re.template.article import Article


class P1433PublishedIn(ClaimFactory):
    """
    Returns the Claim **published in** -> **<item of the category of the issue>**
    """

    def _get_claim_json(self) -> List[JsonClaimDict]:
        return [self.create_claim_json(self.get_volume_snak(self.re_page.splitted_article_list[0]))]

    def get_volume_snak(self, articles: list[Article]) -> SnakParameter:
        return SnakParameter(property_str=self.get_property_string(),
                             target_type="wikibase-item",
                             target=self._volume_of_article(articles[0]).data_item)
