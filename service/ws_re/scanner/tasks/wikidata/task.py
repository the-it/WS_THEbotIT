from typing import Dict, List, Optional

import pywikibot
from pywikibot import ItemPage

from service.ws_re.scanner.tasks.base_task import ReScannerTask
from service.ws_re.scanner.tasks.wikidata.claims._typing import ClaimList, ClaimDictionary, \
    ChangedClaimsDict
from service.ws_re.scanner.tasks.wikidata.claims.non_claims import NonClaims
from service.ws_re.scanner.tasks.wikidata.claims.p1343_described_by_source import P1343DescribedBySource
from service.ws_re.scanner.tasks.wikidata.claims.p1433_published_in import P1433PublishedIn
from service.ws_re.scanner.tasks.wikidata.claims.p1476_title import P1476Title
from service.ws_re.scanner.tasks.wikidata.claims.p155_follows_p156_followed_by import P155Follows, \
    P156FollowedBy
from service.ws_re.scanner.tasks.wikidata.claims.p31_instance_of import P31InstanceOf
from service.ws_re.scanner.tasks.wikidata.claims.p361_part_of import P361PartOf
from service.ws_re.scanner.tasks.wikidata.claims.p3903_column import P3903Column
from service.ws_re.scanner.tasks.wikidata.claims.p407_language_of_work_or_name import \
    P407LanguageOfWorkOrName
from service.ws_re.scanner.tasks.wikidata.claims.p50_author import P50Author
from service.ws_re.scanner.tasks.wikidata.claims.p577_publication_date import P577PublicationDate
from service.ws_re.scanner.tasks.wikidata.claims.p6216_copyright_status import P6216CopyrightStatus
from service.ws_re.scanner.tasks.wikidata.claims.p921_main_subject import P921MainSubject
from tools.bots.pi import WikiLogger

SerializedClaimList = List[Dict]
SerializedClaimDictionary = Dict[str, SerializedClaimList]


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
        self.test_counter_backlink = 0

    def task(self):
        try:
            # edit existing wikidata item
            data_item: pywikibot.ItemPage = self.re_page.page.data_item()
            data_item.get()
            item_dict_add = {}
            # process claims, if they differ
            claims_to_change = self._get_claimes_to_change(data_item)
            if claims_to_change["add"]:
                item_dict_add.update({"claims": self._serialize_claims_to_add(claims_to_change["add"])})
            # process if non claims differ
            non_claims = NonClaims(self.re_page)
            if non_claims.labels_and_sitelinks_has_changed(data_item.toJSON()):
                item_dict_add.update(non_claims.dict)
            # if a diff exists alter the wikidata item
            if item_dict_add:
                data_item.editEntity(data=item_dict_add, summary=self._create_add_summary(item_dict_add))
                self.logger.debug(f"Item ([[d:{data_item.id}]]) for {self.re_page.lemma_as_link} altered.")
            if claims_to_remove := claims_to_change["remove"]:
                # if there are claims, that aren't up to date remove them
                data_item.removeClaims(claims=claims_to_remove, summary=self._create_remove_summary(claims_to_remove))
        except pywikibot.exceptions.NoPageError:
            # create a new one from scratch
            data_item = pywikibot.ItemPage(self.wikidata)
            claims_to_change = self._get_claimes_to_change(None)
            item_dict_add = {"claims": self._serialize_claims_to_add(claims_to_change["add"])}
            item_dict_add.update(NonClaims(self.re_page).dict)
            data_item.editEntity(item_dict_add)
            self.logger.debug(f"Item ([[d:{data_item.id}]]) for {self.re_page.lemma_as_link} created.")
        self.back_link_main_topic()

    def back_link_main_topic(self):
        p1343_factory = P1343DescribedBySource(self.re_page, self.logger)
        main_topic_id = p1343_factory.get_main_topic_id()
        if not main_topic_id:
            return
        main_topic = ItemPage(self.wikidata, f"Q{main_topic_id}")
        claim_dict = p1343_factory.get_claims_to_update(main_topic)
        if claim_dict["add"] or claim_dict["remove"]:
            # only do 20 per day in the beginning
            if self.test_counter_backlink < 20:
                self.logger.info(f"Backlinking {claim_dict['add']} to {main_topic} on {self.re_page.lemma_as_link}")
                if claim_dict["add"]:
                    main_topic.editEntity(data={"claims": self._serialize_claims_to_add(claim_dict["add"])},
                                          summary="Add reference to a lexicon article.")
                if claim_dict["remove"]:
                    main_topic.removeClaims(claims=claim_dict["remove"],
                                            summary="Remove old reference to a lexicon article.")
                self.test_counter_backlink += 1

    @staticmethod
    def _create_remove_summary(claims_to_remove: List[pywikibot.Claim]) -> str:
        summary = []
        for claim in claims_to_remove:
            if claim.id not in summary:
                summary.append(claim.id)
        return ", ".join(summary)

    @staticmethod
    def _create_add_summary(item_dict_add: Dict) -> str:
        summary = []
        if "sitelinks" in item_dict_add:
            summary.append("non_claims")
        try:
            for key in item_dict_add["claims"]:
                summary.append(key)
        except KeyError:
            pass
        return ", ".join(summary)

    # CLAIM functionality

    @staticmethod
    def _serialize_claims_to_add(claims_to_add: ClaimDictionary) -> SerializedClaimDictionary:
        claims_to_add_serialized = {}
        for key, claim_list in claims_to_add.items():
            claims_to_add_serialized[key] = [claim.toJSON() for claim in claim_list]
        return claims_to_add_serialized

    def _get_claimes_to_change(self, data_item: Optional[pywikibot.ItemPage]) -> ChangedClaimsDict:
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
