from typing import List, Optional, Tuple

import pywikibot

from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory
from service.ws_re.scanner.tasks.wikidata.claims._base import SnakParameter
from service.ws_re.scanner.tasks.wikidata.claims._typing import JsonClaimDict, ClaimList
from service.ws_re.scanner.tasks.wikidata.claims.p31_instance_of import P31InstanceOf
from service.ws_re.template.re_page import RePage
from tools.bots.cloud.logger import WikiLogger


class P1343DescribedBySource(ClaimFactory):
    """
    Returns a reversed claim for the target item of P921 main subject.
    """
    MAIN_TOPIC_PROP = "P921"
    DESCRIBED_IN_PROP = "P1343"
    DESCRIBED_OBJECT_PROP = "P805"

    def __init__(self, re_page: RePage, logger: WikiLogger):
        super().__init__(re_page, logger)
        self.data_item_re_source = self.re_page.page.data_item()
        self.claims_re_source = self.data_item_re_source.get()["claims"].toJSON()

    def _get_claim_json(self) -> List[JsonClaimDict]:
        re_item_id = int(self.data_item_re_source.id[1:])
        if target_id := self.get_main_topic_id():
            qualifier_snaks = self.get_qualifiers(re_item_id, target_id)
            if not qualifier_snaks:
                return []
            main_snak = SnakParameter(property_str=self.DESCRIBED_IN_PROP,
                                      target_type="wikibase-item",
                                      target=self.ITEM_RE)
            claim_json = [self.create_claim_json(snak_parameter=main_snak,
                                                 qualifiers=qualifier_snaks,
                                                 references=[[self._IMPORTED_FROM_WIKISOURCE]])]
            return claim_json
        return []

    def get_qualifiers(self, re_item_id: int, target_id: int) -> List[SnakParameter]:
        target_item = pywikibot.ItemPage(self.re_page.page.data_repository, f"Q{target_id}")
        existing_qualifiers = self.get_existing_qualifiers(target_item)
        if re_item_id not in existing_qualifiers:
            existing_qualifiers.append(re_item_id)
        filtered_qualifiers = [qualifier for qualifier in existing_qualifiers
                               if self.check_source_is_valid(qualifier, target_id)]
        qualifier_snaks: list[SnakParameter] = []
        for qualifier in filtered_qualifiers:
            qualifier_snaks.append(
                SnakParameter(property_str=self.DESCRIBED_OBJECT_PROP,
                              target_type="wikibase-item",
                              target=f"Q{qualifier}")
            )
        return qualifier_snaks

    def get_main_topic_id(self) -> Optional[int]:
        if self.MAIN_TOPIC_PROP in self.claims_re_source:
            return int(self.claims_re_source[self.MAIN_TOPIC_PROP][0]['mainsnak']['datavalue']['value']['numeric-id'])
        return None

    def get_existing_qualifiers(self, target_item) -> list[int]:
        target_claims = target_item.get()["claims"].toJSON()
        if self.DESCRIBED_IN_PROP not in target_claims:
            return []
        described_in_claims = target_claims[self.DESCRIBED_IN_PROP]
        filtered_described_in_claims = \
            [claim for claim in described_in_claims
             if claim["mainsnak"]["datavalue"]["value"]["numeric-id"] == int(self.ITEM_RE[1:])]
        existing_qualifiers: list[int] = []
        for claim in filtered_described_in_claims:
            for qualifier in claim["qualifiers"][self.DESCRIBED_OBJECT_PROP]:
                if value := qualifier["datavalue"]["value"]["numeric-id"]:
                    if value not in existing_qualifiers:
                        existing_qualifiers.append(value)
        return existing_qualifiers

    def check_source_is_valid(self, source_id: int, target_id: int) -> bool:
        source_item = pywikibot.ItemPage(self.re_page.page.data_repository, f"Q{source_id}")
        source_claims = source_item.get()["claims"].toJSON()
        # if a reference, this isn't valid
        if (source_claims["P31"][0]["mainsnak"]["datavalue"]["value"]["numeric-id"] == int(
                P31InstanceOf.CROSS_REFERENCE_ITEM[1:])):
            return False
        # no main topic, nothing to check
        if self.MAIN_TOPIC_PROP not in source_claims:
            return False
        main_topic_claims = source_claims[self.MAIN_TOPIC_PROP]
        for claim in main_topic_claims:
            if claim["mainsnak"]["datavalue"]["value"]["numeric-id"] == target_id:
                return True
        return False

    @classmethod
    def filter_new_vs_old_claim_list(cls,
                                     new_claim_list: ClaimList,
                                     old_claim_list: ClaimList) -> Tuple[ClaimList, ClaimList]:
        filtered_new_claims, filtered_old_claim_list = (
            ClaimFactory.filter_new_vs_old_claim_list(new_claim_list, old_claim_list))
        return filtered_new_claims, [claim for claim in filtered_old_claim_list
                                     if claim.target.id == cls.ITEM_RE]
