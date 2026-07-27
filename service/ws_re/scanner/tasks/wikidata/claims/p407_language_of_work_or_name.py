from service.ws_re.scanner.tasks.wikidata.claims._base import SnakParameter
from service.ws_re.scanner.tasks.wikidata.claims._typing import JsonClaimDict
from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory


class P407LanguageOfWorkOrName(ClaimFactory):
    """
    Returns the Claim **language of work or name** -> **german**
    """

    GERMAN = "Q188"

    def _get_claim_json(self) -> list[JsonClaimDict]:
        snak_parameter = SnakParameter(
            property_str=self.get_property_string(), target_type="wikibase-item", target=self.GERMAN
        )
        return [self.create_claim_json(snak_parameter)]
