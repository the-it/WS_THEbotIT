from typing import List

from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory, \
    JsonClaimDict


class P577PublicationDate(ClaimFactory):
    """
    Returns the Claim **publication date** -> **<Year of publication of RE lemma>**
    """

    def _get_claim_json(self) -> List[JsonClaimDict]:
        return [self.create_claim_json(self.get_property_string(),
                                       "time",
                                       self._volume_of_first_article.year)]
