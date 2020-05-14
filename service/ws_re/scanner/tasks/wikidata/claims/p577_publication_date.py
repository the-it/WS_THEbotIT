from typing import List

from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory, \
    JsonClaimDict, SnakParameter


class P577PublicationDate(ClaimFactory):
    """
    Returns the Claim **publication date** -> **<Year of publication of RE lemma>**
    """

    def _get_claim_json(self) -> List[JsonClaimDict]:
        snak = SnakParameter(property_str=self.get_property_string(),
                             target_type="time",
                             target=self._volume_of_first_article.year)
        return [self.create_claim_json(snak)]
