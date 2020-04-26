from typing import List

from scripts.service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory, \
    JsonClaimDict


class P361PartOf(ClaimFactory):
    """
    Returns the Claim **part of** -> **Paulys Realenzyklopädie der klassischen Altertumswissenschaft**
    """

    ITEM_RE = "Q1138524"

    def _get_claim_json(self) -> List[JsonClaimDict]:
        return [self.create_claim_json(self.get_property_string(), "wikibase-item", self.ITEM_RE)]
