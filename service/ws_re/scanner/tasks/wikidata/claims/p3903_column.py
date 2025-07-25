from typing import List

from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory
from service.ws_re.scanner.tasks.wikidata.claims._base import SnakParameter
from service.ws_re.scanner.tasks.wikidata.claims._typing import JsonClaimDict
from service.ws_re.template.article import Article


class P3903Column(ClaimFactory):
    """
    Returns the Claim **column** -> **<start column>[–<end column>]**
    """

    def _get_claim_json(self) -> List[JsonClaimDict]:
        return [self.create_claim_json(self.get_column_snak(self.re_page.first_article))]

    def get_column_snak(self, article: Article) -> SnakParameter:
        start = str(article["SPALTE_START"].value)
        end: str = ""
        if article["SPALTE_END"].value not in ("", "OFF"):
            end = str(article["SPALTE_END"].value)
        columns = start
        if end and start != end:
            columns = f"{start}–{end}"
        return SnakParameter(property_str=self.get_property_string(),
                             target_type="string",
                             target=columns)
