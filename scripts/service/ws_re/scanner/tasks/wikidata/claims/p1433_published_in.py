from typing import List

from scripts.service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory, \
    JsonClaimDict


class P1433PublishedIn(ClaimFactory):
    """
    Returns the Claim **published in** -> **<item of the category of the issue>**
    """

    def _get_claim_json(self) -> List[JsonClaimDict]:
        return [self.create_claim_json(self.get_property_string(),
                                       "wikibase-item",
                                       self._volume_of_first_article.data_item)]
