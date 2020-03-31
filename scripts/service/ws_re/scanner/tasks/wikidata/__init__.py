import json
from pathlib import Path
from string import Template
from typing import Dict, Callable

import dictdiffer
import pywikibot

from scripts.service.ws_re.scanner import ReScannerTask
from tools.bots.pi import WikiLogger


class DATATask(ReScannerTask):
    _languages = ("de", "en", "fr", "nl")

    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        ReScannerTask.__init__(self, wiki, logger, debug)
        self.wikidata: pywikibot.site.DataSite = pywikibot.Site(code="wikidata", fam="wikidata", user="THEbotIT")
        with open(Path(__file__).parent.joinpath("non_claims.json")) as non_claims_json:
            self._non_claims_template = Template(non_claims_json.read())

    def task(self):
        try:
            # edit existing wikidata item
            data_item: pywikibot.ItemPage = self.re_page.page.data_item()
            self._update_non_claims(data_item)
        except pywikibot.NoPage:
            # create a new one from scratch
            data_item: pywikibot.ItemPage = self.wikidata.createNewItemFromPage(page=self.re_page.page)

        self._get_claim_functions()
        # data_item.editEntity(new_values)

        # data_item.save()

    # NON CLAIM functionality

    def _update_non_claims(self, item: pywikibot.ItemPage):
        non_claims = self._non_claims
        if self._labels_and_sitelinks_has_changed(item, non_claims):
            item.editEntity(non_claims)

    @property
    def _non_claims(self) -> Dict:
        replaced_json = self._non_claims_template.substitute(lemma=self.re_page.lemma_without_prefix,
                                                                 lemma_with_prefix=self.re_page.lemma)
        non_claims = json.loads(replaced_json)
        return non_claims

    def _labels_and_sitelinks_has_changed(self, item: pywikibot.ItemPage, new_non_claims: Dict) -> bool:
        old_non_claims = item.toJSON()
        # claims are not relevant here
        del old_non_claims["claims"]
        # reformat sitelinks (toJSON has different format then editEntity accepts)
        old_non_claims["sitelinks"] = [sitelink for sitelink in old_non_claims["sitelinks"].values()]
        # remove all languages, that are not set by this bot
        for labels_or_descriptions in ("labels", "descriptions"):
            old_non_claims[labels_or_descriptions] = {key: value
                                                          for (key, value)
                                                          in old_non_claims[labels_or_descriptions].items()
                                                          if key in self._languages}
        return bool(tuple(dictdiffer.diff(new_non_claims, old_non_claims)))

    # CLAIM functionality

    def _get_claim_functions(self) -> Dict[str, Callable]:
        """
        Returns a dictionary of claim generation functions. The key represents the name of the claim.
        Each function will return a pywikibot.Claim. The functions are parsed by their name. So every function that
        returns a propery
        """
        claim_functions = {}
        for item in dir(self):
            if "_p" in item:
                claim_functions[item[1:].upper()] = getattr(self, item)
        return claim_functions

    # from here on all functions are related to one specific claim
    def _p31(self) -> pywikibot.Claim:
        claim = pywikibot.Claim(self.wikidata, 'P31')
        target = pywikibot.ItemPage(self.wikidata, "Q13433827")
        claim.setTarget(target)
        return claim
