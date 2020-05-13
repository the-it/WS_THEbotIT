from typing import List

from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory, \
    JsonClaimDict, SnakParameter


class P407LanguageOfWorkOrName(ClaimFactory):
    """
    Returns the Claim **language of work or name** -> **german**
    """
    GERMAN = "Q188"

    def _get_claim_json(self) -> List[JsonClaimDict]:
        snak_parameter = SnakParameter(property_str=self.get_property_string(),
                                       target_type="wikibase-item",
                                       target=self.GERMAN)
        return [self.create_claim_json(snak_parameter)]
