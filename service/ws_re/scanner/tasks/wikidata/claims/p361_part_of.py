from typing import List

from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory
from service.ws_re.scanner.tasks.wikidata.claims._base import SnakParameter
from service.ws_re.scanner.tasks.wikidata.claims._typing import JsonClaimDict


class P361PartOf(ClaimFactory):
    """
    Returns the Claim **part of** -> **Paulys Realenzyklopädie der klassischen Altertumswissenschaft**
    """

    ITEM_RE = "Q1138524"

    def _get_claim_json(self) -> List[JsonClaimDict]:
        snak_parameter = SnakParameter(property_str=self.get_property_string(),
                                       target_type="wikibase-item",
                                       target=self.ITEM_RE)
        return [self.create_claim_json(snak_parameter)]
