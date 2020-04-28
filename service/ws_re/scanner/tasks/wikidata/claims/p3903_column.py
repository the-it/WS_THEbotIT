from typing import List

from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory, \
    JsonClaimDict


class P3903Column(ClaimFactory):
    """
    Returns the Claim **column** -> **<start column>[–<end column>]**
    """

    def _get_claim_json(self) -> List[JsonClaimDict]:
        start = str(self._first_article["SPALTE_START"].value)
        end: str = ""
        if self._first_article["SPALTE_END"].value not in ("", "OFF"):
            end = str(self._first_article["SPALTE_END"].value)
        columns = start
        if end and start != end:
            columns = f"{start}–{end}"
        return [self.create_claim_json(self.get_property_string(), "string", columns)]
