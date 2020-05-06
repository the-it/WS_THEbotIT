import re
from typing import List

from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory, \
    JsonClaimDict, SnakParameter


class P1680Subtitle(ClaimFactory):
    """
    Returns the Claim **subtitle** -> **<subtitle of the RE lemma>**

    example: If the lemma starts with "'''Bizone''' ({{Polytonisch|Βιζώνη}})", the subtitle is "Βιζώνη".
    """

    def _get_claim_json(self) -> List[JsonClaimDict]:
        subtitle_hit = re.search(r"\(([^)]*)\)", self._first_article.text[:50])
        if subtitle_hit:
            subtitle = self._strip_template(subtitle_hit.group(1))
            snak_parameter = SnakParameter(property_str=self.get_property_string(),
                                           target_type="monolingualtext",
                                           target=subtitle)
            return [self.create_claim_json(snak_parameter)]
        return []

    def _strip_template(self, text: str):
        hit = re.search(r"^\{\{[^\}\|]*\|([^\}]*)\}\}$", text)
        if hit:
            return hit.group(1)
        return text
