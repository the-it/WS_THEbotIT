from typing import List

from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory, \
    JsonClaimDict, SnakParameter


class P1476Title(ClaimFactory):
    """
    Returns the Claim **title** -> **<title for the RE lemma>**
    """

    def _get_claim_json(self) -> List[JsonClaimDict]:
        snak_parameter = SnakParameter(property_str=self.get_property_string(),
                                       target_type="monolingualtext",
                                       target=self.re_page.lemma_without_prefix)
        return [self.create_claim_json(snak_parameter)]
