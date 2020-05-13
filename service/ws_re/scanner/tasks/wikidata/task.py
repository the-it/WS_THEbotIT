import json
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from string import Template
from typing import Dict, List, Optional

import dictdiffer
import pywikibot

from service.ws_re.scanner.tasks.base_task import ReScannerTask
from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimDictionary, \
    SerializedClaimDictionary, ClaimList, ChangedClaimsDict
from service.ws_re.scanner.tasks.wikidata.claims.p1433_published_in import P1433PublishedIn
from service.ws_re.scanner.tasks.wikidata.claims.p1476_title import P1476Title
from service.ws_re.scanner.tasks.wikidata.claims.p155_follows_p156_followed_by import P155Follows, \
    P156FollowedBy
from service.ws_re.scanner.tasks.wikidata.claims.p31_instance_of import P31InstanceOf
from service.ws_re.scanner.tasks.wikidata.claims.p361_part_of import P361PartOf
from service.ws_re.scanner.tasks.wikidata.claims.p3903_column import P3903Column
from service.ws_re.scanner.tasks.wikidata.claims.p407_language_of_work_or_name import P407LanguageOfWorkOrName
from service.ws_re.scanner.tasks.wikidata.claims.p50_author import P50Author
from service.ws_re.scanner.tasks.wikidata.claims.p577_publication_date import P577PublicationDate
from service.ws_re.scanner.tasks.wikidata.claims.p6216_copyright_status import P6216CopyrightStatus
from service.ws_re.scanner.tasks.wikidata.claims.p921_main_subject import P921MainSubject
from tools.bots.pi import WikiLogger


class DATATask(ReScannerTask):
    claim_factories = (
        P31InstanceOf,
        P50Author,
        P155Follows,
        P156FollowedBy,
        P361PartOf,
        P407LanguageOfWorkOrName,
        P577PublicationDate,
        P921MainSubject,
        P1433PublishedIn,
        P1476Title,
        P3903Column,
        P6216CopyrightStatus,
    )

    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        ReScannerTask.__init__(self, wiki, logger, debug)
        self.wikidata: pywikibot.Site = pywikibot.Site(code="wikidata", fam="wikidata", user="THEbotIT")
        with open(Path(__file__).parent.joinpath("non_claims_article.json")) as non_claims_json:
            self._non_claims_template_article = Template(non_claims_json.read())
        with open(Path(__file__).parent.joinpath("non_claims_crossref.json")) as non_claims_json:
            self._non_claims_template_crossref = Template(non_claims_json.read())
        # debug functions
        self._counter = 0

    def task(self):
        start_time = datetime.now()
        if self._counter < 100:
            try:
                try:
                    # edit existing wikidata item
                    data_item: pywikibot.ItemPage = self.re_page.page.data_item()
                    # todo: remove this. But for testing only new creations
                    return
                    data_item.get()
                    item_dict_add = {}
                    # process claims, if they differ
                    claims_to_change = self._get_claimes_to_change(data_item)
                    if claims_to_change["remove"]:
                        # if there are claims, that aren't up to date remove them
                        data_item.removeClaims(claims_to_change["remove"])
                    if claims_to_change["add"]:
                        item_dict_add.update({"claims": self._serialize_claims_to_add(claims_to_change["add"])})
                    # process if non claims differ
                    # todo: detection for diffs not working correctly, ok for save edits, bad dor requests
                    if self._labels_and_sitelinks_has_changed(data_item.toJSON(), self._non_claims):
                        item_dict_add.update(self._non_claims)
                    # if a diff exists alter the wikidata item
                    if item_dict_add:
                        data_item.editEntity(item_dict_add)
                        self._counter += 1
                        self.logger.info(f"Item ([[d:{data_item.id}]]) for {self.re_page.lemma_as_link} altered.")
                except pywikibot.exceptions.NoPage:
                    # create a new one from scratch
                    data_item: pywikibot.ItemPage = pywikibot.ItemPage(self.wikidata)
                    claims_to_change = self._get_claimes_to_change(None)
                    item_dict_add = {"claims": self._serialize_claims_to_add(claims_to_change["add"])}
                    item_dict_add.update(self._non_claims)
                    data_item.editEntity(item_dict_add)
                    self._counter += 1
                    self.logger.info(f"Item ([[d:{data_item.id}]]) for {self.re_page.lemma_as_link} created.")
            except pywikibot.exceptions.MaxlagTimeoutError:
                self.logger.error(f"MaxlagTimeoutError for {self.re_page.lemma_as_link}"
                                  f", after {datetime.now() - start_time}")

    # NON CLAIM functionality

    @property
    def _non_claims(self) -> Dict:
        if self.re_page[0]["VERWEIS"].value:
            replaced_json = self._non_claims_template_crossref.substitute(lemma=self.re_page.lemma_without_prefix,
                                                                          lemma_with_prefix=self.re_page.lemma)
        else:
            replaced_json = self._non_claims_template_article.substitute(lemma=self.re_page.lemma_without_prefix,
                                                                         lemma_with_prefix=self.re_page.lemma)
        non_claims: Dict = json.loads(replaced_json)
        return non_claims

    @property
    def _languages(self) -> List[str]:
        return [str(language) for language in self._non_claims["labels"].keys()]

    def _labels_and_sitelinks_has_changed(self, old_non_claims: Dict, new_non_claims: Dict) -> bool:
        # claims are not relevant here
        with suppress(KeyError):
            del old_non_claims["claims"]
        # reformat sitelinks (toJSON has different format then editEntity accepts)
        old_non_claims["sitelinks"] = list(old_non_claims["sitelinks"].values())
        # remove all languages, that are not set by this bot
        for labels_or_descriptions in ("labels", "descriptions"):
            old_non_claims[labels_or_descriptions] = {key: value
                                                      for (key, value)
                                                      in old_non_claims[labels_or_descriptions].items()
                                                      if key in self._languages}
        return bool(tuple(dictdiffer.diff(new_non_claims, old_non_claims)))

    # CLAIM functionality

    @staticmethod
    def _serialize_claims_to_add(claims_to_add: ClaimDictionary) -> SerializedClaimDictionary:
        claims_to_add_serialized = {}
        for key, claim_list in claims_to_add.items():
            claim_list_serialized = []
            for claim in claim_list:
                claim_list_serialized.append(claim.toJSON())
            claims_to_add_serialized[key] = [claim.toJSON() for claim in claim_list]
        return claims_to_add_serialized

    def _get_claimes_to_change(self, data_item: Optional[pywikibot.ItemPage]) \
        -> ChangedClaimsDict:
        """
        Iterates through all claim factories and aggregates the claims, that should be remove, and the claims, that
        should be added.

        :param data_item: current
        :return:
        """
        claims_to_add: ClaimDictionary = {}
        claims_to_remove: ClaimList = []
        for claim_factory_class in self.claim_factories:
            claim_factory = claim_factory_class(self.re_page, self.logger)
            claims_to_change_dict = claim_factory.get_claims_to_update(data_item)
            if claims_to_change_dict["add"]:
                claims_to_add.update(claims_to_change_dict["add"])
            if claims_to_change_dict["remove"]:
                claims_to_remove += claims_to_change_dict["remove"]
        return {"add": claims_to_add, "remove": claims_to_remove}
