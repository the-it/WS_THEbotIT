from typing import List

from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory
from service.ws_re.scanner.tasks.wikidata.claims._base import SnakParameter
from service.ws_re.scanner.tasks.wikidata.claims._typing import JsonClaimDict
from service.ws_re.template.article import Article


class P577PublicationDate(ClaimFactory):
    """
    Returns the Claim **publication date** -> **<Year of publication of RE lemma>**
    """

    def _get_claim_json(self) -> List[JsonClaimDict]:
        return [self.create_claim_json(self.get_snack(self.re_page.first_article))]

    def get_snack(self, article: Article) -> SnakParameter:
        return SnakParameter(property_str=self.get_property_string(),
                             target_type="time",
                             target=self._volume_of_article(article).year)
