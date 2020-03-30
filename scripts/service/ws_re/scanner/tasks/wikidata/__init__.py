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
        with open(Path(__file__).parent.joinpath("non_properties.json")) as non_properties_json:
            self._non_properties_template = Template(non_properties_json.read())

    def task(self):
        try:
            # edit existing wikidata item
            data_item: pywikibot.ItemPage = self.re_page.page.data_item()
            self._update_non_properties(data_item)
        except pywikibot.NoPage:
            # create a new one from scratch
            data_item: pywikibot.ItemPage = self.wikidata.createNewItemFromPage(page=self.re_page.page)

        self._get_property_functions()
        # data_item.editEntity(new_values)

        # data_item.save()

    # NON PROPERTIES functionality

    def _update_non_properties(self, item: pywikibot.ItemPage):
        non_properties = self._non_properties
        if self._labels_and_sitelinks_has_changed(item, non_properties):
            item.editEntity(non_properties)

    @property
    def _non_properties(self) -> Dict:
        replaced_json = self._non_properties_template.substitute(lemma=self.re_page.lemma_without_prefix,
                                                                 lemma_with_prefix=self.re_page.lemma)
        non_properties = json.loads(replaced_json)
        return non_properties

    def _labels_and_sitelinks_has_changed(self, item: pywikibot.ItemPage, new_non_properties: Dict) -> bool:
        old_non_properties = item.toJSON()
        # claims are not relevant here
        del old_non_properties["claims"]
        # reformat sitelinks (toJSON has different format then editEntity accepts)
        old_non_properties["sitelinks"] = [sitelink for sitelink in old_non_properties["sitelinks"].values()]
        # remove all languages, that are not set by this bot
        for labels_or_descriptions in ("labels", "descriptions"):
            old_non_properties[labels_or_descriptions] = {key: value
                                                          for (key, value)
                                                          in old_non_properties[labels_or_descriptions].items()
                                                          if key in self._languages}
        return bool(tuple(dictdiffer.diff(new_non_properties, old_non_properties)))

    # PROPERTIES functionality

    def _get_property_functions(self) -> Dict[str, Callable]:
        property_functions = {}
        for item in dir(self):
            if "_p" in item:
                property_functions[item[1:].upper()] = getattr(self, item)
        return property_functions

    # from here on all functions are related to one specific property
    def _p31(self) -> pywikibot.Claim:
        claim = pywikibot.Claim(self.wikidata, 'P31')
        target = pywikibot.ItemPage(self.wikidata, "Q13433827")
        claim.setTarget(target)
        return claim
