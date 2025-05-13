from typing import List

import pywikibot

from service.ws_re.scanner.tasks.base import get_redirect
from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory
from service.ws_re.scanner.tasks.wikidata.claims._base import SnakParameter
from service.ws_re.scanner.tasks.wikidata.claims._typing import JsonClaimDict
from service.ws_re.template.re_page import RePage
from tools.bots.cloud.logger import WikiLogger


class P13269DirectsReadersTo(ClaimFactory):
    """
    Returns the Claim **directs readers to** -> **object of the RE lemma, that actually describes the topic**
    """

    def __init__(self, re_page: RePage, logger: WikiLogger):
        super().__init__(re_page, logger)
        self.debug_counter = 0

    def _get_claim_json(self) -> List[JsonClaimDict]:
        if self.debug_counter > 20:
            # create only 20 items per night in the start phase
            return []
        redirect = get_redirect(self.re_page.first_article)
        if redirect and isinstance(redirect, str):
            redirected_lemma = pywikibot.Page(self.re_page.page.site, f"RE:{redirect}")
            if redirected_lemma.exists():
                data_item = redirected_lemma.data_item()
                if data_item.exists():
                    self.debug_counter += 1
                    self.logger.info(f"{self.re_page.lemma_as_link} -> {redirected_lemma.title(as_link=True)}")
                    snak_parameter = SnakParameter(property_str=self.get_property_string(),
                                                   target_type="wikibase-item",
                                                   target=data_item.id)
                    return [self.create_claim_json(snak_parameter)]
        return []
