from typing import List

from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory
from service.ws_re.scanner.tasks.wikidata.claims._base import SnakParameter
from service.ws_re.scanner.tasks.wikidata.claims._typing import JsonClaimDict


class P1433PublishedIn(ClaimFactory):
    """
    Returns the Claim **published in** -> **<item of the category of the issue>**
    """

    def _get_claim_json(self) -> List[JsonClaimDict]:
        snak_parameter = SnakParameter(property_str=self.get_property_string(),
                                       target_type="wikibase-item",
                                       target=self._volume_of_first_article.data_item)
        return [self.create_claim_json(snak_parameter)]
