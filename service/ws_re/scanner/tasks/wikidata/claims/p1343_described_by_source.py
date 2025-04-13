from typing import List, Optional

from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory
from service.ws_re.scanner.tasks.wikidata.claims._base import SnakParameter
from service.ws_re.scanner.tasks.wikidata.claims._typing import JsonClaimDict
from service.ws_re.template.re_page import RePage
from tools.bots.pi import WikiLogger


class P1343DescribedBySource(ClaimFactory):
    """
    Returns a reversed claim for the target item of P921 main subject.
    """
    MAIN_TOPIC_PROP = "P921"
    DESCRIBED_IN_PROP = "P1343"
    DESCRIBED_OBJECT_PROP = "P805"

    def __init__(self, re_page: RePage, logger: WikiLogger):
        super().__init__(re_page, logger)
        self.data_item = self.re_page.page.data_item()
        self.claims = self.data_item.get()["claims"].toJSON()

    def _get_claim_json(self) -> List[JsonClaimDict]:
        re_id = self.data_item.id
        if self.get_main_topic():
            main_snak = SnakParameter(property_str=self.DESCRIBED_IN_PROP,
                                      target_type="wikibase-item",
                                      target=self.ITEM_RE)
            qualifier_snak = SnakParameter(property_str=self.DESCRIBED_OBJECT_PROP,
                                           target_type="wikibase-item",
                                           target=re_id)
            return [self.create_claim_json(snak_parameter=main_snak,
                                           qualifiers=[qualifier_snak],
                                           references=[[self._IMPORTED_FROM_WIKISOURCE]])]
        return []

    def get_main_topic(self) -> Optional[str]:
        if self.MAIN_TOPIC_PROP in self.claims:
            return f"Q{self.claims[self.MAIN_TOPIC_PROP][0]['mainsnak']
                       ['datavalue']['value']['numeric-id']}"
        return None
