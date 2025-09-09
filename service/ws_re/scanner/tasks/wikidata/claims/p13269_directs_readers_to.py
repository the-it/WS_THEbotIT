from typing import List

import pywikibot

from service.ws_re.scanner.tasks.base import get_redirect
from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory
from service.ws_re.scanner.tasks.wikidata.claims._base import SnakParameter
from service.ws_re.scanner.tasks.wikidata.claims._typing import JsonClaimDict


class P13269DirectsReadersTo(ClaimFactory):
    """
    Returns the Claim **directs readers to** -> **object of the RE lemma, that actually describes the topic**
    """

    def _get_claim_json(self) -> List[JsonClaimDict]:
        redirect = get_redirect(self.re_page.first_article)
        if redirect and isinstance(redirect, str):
            redirected_lemma = pywikibot.Page(self.re_page.page.site, f"RE:{redirect}")
            if redirected_lemma.exists():
                try:
                    data_item = redirected_lemma.data_item()
                except pywikibot.exceptions.NoPageError:
                    self.logger.error(f"{self.get_property_string()}: "
                                      f"Page existed for {redirected_lemma}, but no data item.")
                    return []
                if data_item.exists():
                    snak_parameter = SnakParameter(property_str=self.get_property_string(),
                                                   target_type="wikibase-item",
                                                   target=data_item.id)
                    return [self.create_claim_json(snak_parameter)]
        return []
