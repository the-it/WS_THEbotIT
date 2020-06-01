from typing import List

from service.ws_re.scanner.tasks.wikidata.claims._typing import JsonClaimDict
from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory


class P1476Title(ClaimFactory):
    """
    Empties the title claim, was kind of a bad idea
    """

    def _get_claim_json(self) -> List[JsonClaimDict]:
        return []
