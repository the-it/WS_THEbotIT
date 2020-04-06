import json
import re
from datetime import datetime
from pathlib import Path
from string import Template
from typing import Dict, Callable, List, Optional, Tuple

import dictdiffer
import pywikibot

from scripts.service.ws_re.register.author import Author
from scripts.service.ws_re.register.authors import Authors
from scripts.service.ws_re.scanner import ReScannerTask
from scripts.service.ws_re.scanner.tasks.wikidata.copyright_status_claims import PublicDomainClaims
from scripts.service.ws_re.template.article import Article
from scripts.service.ws_re.volumes import Volumes, Volume
from tools.bots.pi import WikiLogger


class DATATask(ReScannerTask):
    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        ReScannerTask.__init__(self, wiki, logger, debug)
        self.wikidata: pywikibot.Site = pywikibot.Site(code="wikidata", fam="wikidata", user="THEbotIT")
        with open(Path(__file__).parent.joinpath("non_claims.json")) as non_claims_json:
            self._non_claims_template = Template(non_claims_json.read())
        self._claim_functions = self._get_claim_functions()
        self._authors = Authors()
        self._first_article: Article
        self._volumes = Volumes()
        self._current_year = datetime.now().year
        self._public_domain_claims = PublicDomainClaims(self.wikidata)
        # debug functions
        self._counter = 0

    def task(self):
        self._first_article = self.re_page[0]
        start_time = datetime.now()
        if self._counter < 50:
            try:
                try:
                    # edit existing wikidata item
                    data_item: pywikibot.ItemPage = self.re_page.page.data_item()
                    data_item.get()
                    self._update_non_claims(data_item)
                    claims_to_add, claims_to_remove = self._get_claimes_to_change(data_item)
                    data_item.removeClaims(claims_to_remove)
                    item_dict_add = {"claims": self._serialize_claims_to_add(claims_to_add)}
                    item_dict_add.update(self._non_claims)
                    data_item.editEntity(item_dict_add)
                    self._counter += 1
                    self.logger.info(f"Item ([[d:{data_item.id}]]) for {self.re_page.lemma_as_link} altered.")
                except pywikibot.exceptions.NoPage:
                    # create a new one from scratch
                    data_item: pywikibot.ItemPage = pywikibot.ItemPage(self.wikidata)
                    claims_to_add, _ = self._get_claimes_to_change(None)
                    item_dict_add = {"claims": self._serialize_claims_to_add(claims_to_add)}
                    item_dict_add.update(self._non_claims)
                    data_item.editEntity(item_dict_add)
                    self._counter += 1
                    self.logger.info(f"Item ([[d:{data_item.id}]]) for {self.re_page.lemma_as_link} created.")
            except pywikibot.exceptions.MaxlagTimeoutError:
                self.logger.error(f"MaxlagTimeoutError for {self.re_page.lemma_as_link}"
                                  f", after {datetime.now() - start_time}")

    # NON CLAIM functionality

    def _update_non_claims(self, item: pywikibot.ItemPage):
        non_claims = self._non_claims
        if self._labels_and_sitelinks_has_changed(item, non_claims):
            item.editEntity(non_claims)

    @property
    def _non_claims(self) -> Dict:
        replaced_json = self._non_claims_template.substitute(lemma=self.re_page.lemma_without_prefix,
                                                             lemma_with_prefix=self.re_page.lemma)
        non_claims: Dict = json.loads(replaced_json)
        return non_claims

    @property
    def _languages(self) -> List[str]:
        return [str(language) for language in self._non_claims["labels"].keys()]

    def _labels_and_sitelinks_has_changed(self, item: pywikibot.ItemPage, new_non_claims: Dict) -> bool:
        old_non_claims = item.toJSON()
        # claims are not relevant here
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

    def _get_claim_functions(self) -> Dict[str, Callable]:
        """
        Returns a dictionary of claim generation functions. The key represents the name of the claim.
        Each function will return a pywikibot.Claim. The functions are parsed by their name. So every function that
        returns a claim must be names as _pXXXX.
        """
        claim_functions = {}
        for item in dir(self):
            if re.search(r"^p\d{1,6}", item):
                claim_functions[item.upper()] = getattr(self, item)
        return claim_functions

    @staticmethod
    def _serialize_claims_to_add(claims_to_add) -> Dict[str, List[Dict]]:
        claims_to_add_serialized = {}
        for key, claim_list in claims_to_add.items():
            claim_list_serialized = []
            for claim in claim_list:
                claim_list_serialized.append(claim.toJSON())
            claims_to_add_serialized[key] = claim_list_serialized
        return claims_to_add_serialized

    def _get_claimes_to_change(self, data_item: Optional[pywikibot.ItemPage]) \
        -> Tuple[Dict[str, List[pywikibot.Claim]], List[pywikibot.Claim]]:
        claims_to_add: Dict[str, List[pywikibot.Claim]] = {}
        claims_to_remove: List[pywikibot.Claim] = []
        for claim_str, claim_function in self._claim_functions.items():
            new_claim_list = claim_function()
            if data_item:
                try:
                    old_claim_list = data_item.claims[claim_str]
                except KeyError:
                    old_claim_list = []
            else:
                old_claim_list = []
            if self._claim_list_has_changed(new_claim_list, old_claim_list):
                claims_to_add[claim_str] = new_claim_list
                claims_to_remove += old_claim_list
        return claims_to_add, claims_to_remove

    def _claim_list_has_changed(self, new_claim_list: List[pywikibot.Claim],
                                old_claim_list: List[pywikibot.Claim]) -> bool:
        new_processed_claim_list = self._preprocess_claim_list(new_claim_list)
        old_processed_claim_list = self._preprocess_claim_list(old_claim_list)
        return bool(tuple(dictdiffer.diff(new_processed_claim_list, old_processed_claim_list)))

    @staticmethod
    def _preprocess_claim_list(claim_list: List[pywikibot.Claim]) -> List[Dict]:
        processed_claim_list = []
        for claim_object in claim_list:
            processed_claim = claim_object.toJSON()
            if "id" in processed_claim:
                del processed_claim["id"]
            processed_claim_list.append(processed_claim)
        return processed_claim_list

    # CLAIM FACTORIES from here on all functions are related to one specific claim

    def p31(self) -> List[pywikibot.Claim]:
        """
        Returns the Claim **instance of** -> **encyclopedic article**
        """
        claim = pywikibot.Claim(self.wikidata, 'P31')
        target = pywikibot.ItemPage(self.wikidata, "Q13433827")
        claim.setTarget(target)
        return [claim]

    def p50(self) -> List[pywikibot.Claim]:
        """
        Returns the Claim **author** -> **<Item of author of RE lemma>**
        """
        author_items = self._p50_get_author_list()
        claim_list: List[pywikibot.Claim] = []
        for author in author_items:
            claim = pywikibot.Claim(self.wikidata, 'P50')
            claim.setTarget(author)
            claim_list.append(claim)
        return claim_list

    def _p50_get_author_list(self) -> List[pywikibot.Claim]:
        author_items: List[pywikibot.Claim] = []
        for author in self._authors_of_first_article:
            author_lemma = pywikibot.Page(self.wiki, author.name)
            if not author_lemma.exists():
                continue
            try:
                # append the item of the author, if it exists
                author_items.append(author_lemma.data_item())
            except pywikibot.NoPage:
                continue
        return author_items

    @property
    def _authors_of_first_article(self) -> List[Author]:
        author_list: List[Author] = []
        for article_part in self.re_page.splitted_article_list[0]:
            if isinstance(article_part, str):
                continue
            author = article_part.author[0]
            band = self._first_article["BAND"].value
            possible_authors = self._authors.get_author_by_mapping(author, band)
            if len(possible_authors) == 1:
                author_list.append(possible_authors[0])
        return author_list

    def p155(self) -> List[pywikibot.Claim]:
        """
        Returns the Claim **follows** -> **<Item of predecessor article>**
        """
        lemma_before_this_str = f"RE:{self._first_article['VORGÄNGER'].value}"
        lemma_before_this = pywikibot.Page(self.wiki, lemma_before_this_str)
        try:
            item_before_this = lemma_before_this.data_item()
            claim = pywikibot.Claim(self.wikidata, 'P155')
            claim.setTarget(item_before_this)
            return [claim]
        except pywikibot.NoPage:
            return []

    def p156(self) -> List[pywikibot.Claim]:
        """
        Returns the Claim **followed by** -> **<Item of following article>**
        """
        lemma_after_this_str = f"RE:{self._first_article['NACHFOLGER'].value}"
        lemma_after_this = pywikibot.Page(self.wiki, lemma_after_this_str)
        try:
            item_after_this = lemma_after_this.data_item()
            claim = pywikibot.Claim(self.wikidata, 'P156')
            claim.setTarget(item_after_this)
            return [claim]
        except pywikibot.NoPage:
            return []

    def p361(self) -> List[pywikibot.Claim]:
        """
        Returns the Claim **part of** -> **Paulys Realenzyklopädie der klassischen Altertumswissenschaft**
        """
        claim = pywikibot.Claim(self.wikidata, 'P361')
        target = pywikibot.ItemPage(self.wikidata, "Q1138524")
        claim.setTarget(target)
        return [claim]

    def p577(self) -> List[pywikibot.Claim]:
        """
        Returns the Claim **publication date** -> **<Year of publication of RE lemma>**
        """
        claim = pywikibot.Claim(self.wikidata, 'P577')
        claim.setTarget(pywikibot.WbTime(year=int(self._volume_of_first_article.year)))
        return [claim]

    @property
    def _volume_of_first_article(self) -> Volume:
        return self._volumes[str(self._first_article["BAND"].value)]

    def p921(self) -> List[pywikibot.Claim]:
        """
        Returns the Claim **main subject** -> **<Item of wikipedia article>**
        """
        wp_article = str(self._first_article["WIKIPEDIA"].value)
        # if no wp_article is present, there is nothing to connect
        if not wp_article:
            return []
        # handle the case of an implicit de:
        if ":" not in wp_article:
            wp_article = f"de:{wp_article}"
        language, wp_page_str = wp_article.split(":")
        wp_site: pywikibot.Site = pywikibot.Site(code=language, fam="wikipedia")
        wp_page: pywikibot.Page = pywikibot.Page(wp_site, wp_page_str)
        # try to fetch the data item of the page, if not there is nothing to connect
        try:
            wp_data_item: pywikibot.ItemPage = wp_page.data_item()
        except pywikibot.NoPage:
            return []
        # finally create the claim
        claim = pywikibot.Claim(self.wikidata, 'P921')
        claim.setTarget(wp_data_item)
        return [claim]

    def p1433(self) -> List[pywikibot.Claim]:
        """
        Returns the Claim **published in** -> **<item of the category of the issue>**
        """
        claim = pywikibot.Claim(self.wikidata, 'P1433')
        data_item = pywikibot.ItemPage(self.wikidata, self._volume_of_first_article.data_item)
        claim.setTarget(data_item)
        return [claim]

    def p3903(self) -> List[pywikibot.Claim]:
        """
        Returns the Claim **column** -> **<start column>[–<end column>]**
        """
        claim = pywikibot.Claim(self.wikidata, 'P3903')
        start = str(self._first_article["SPALTE_START"].value)
        end: str = ""
        if self._first_article["SPALTE_START"].value not in ("", "OFF"):
            end = str(self._first_article["SPALTE_START"].value)
        target = start
        if end and start != end:
            target = f"{start}–{end}"
        claim.setTarget(target)
        return [claim]

    def p6216(self) -> List[pywikibot.Claim]:
        """
        Returns the Claim **copyright status** ->
        **<public domain statements dependend on publication age and death of author>**
        """
        claim_list: List[pywikibot.Claim] = []
        if self._current_year - int(self._volume_of_first_article.year) > 95:
            claim_list.append(self._public_domain_claims.CLAIM_PUBLISHED_95_YEARS_AGO)
        pma_claim = self._6216_min_years_since_death
        if pma_claim:
            claim_list.append(pma_claim)
        if self._first_article["KEINE_SCHÖPFUNGSHÖHE"].value:
            claim_list.append(self._public_domain_claims.CLAIM_THRESHOLD_OF_ORIGINALITY)
        return claim_list

    @property
    def _6216_min_years_since_death(self) -> Optional[pywikibot.Claim]:
        max_death_year = 0
        for author in self._authors_of_first_article:
            if not author.death:
                max_death_year = self._current_year
            elif author.death > max_death_year:
                max_death_year = author.death
        years_since_death = self._current_year - max_death_year
        if years_since_death > 100:
            return self._public_domain_claims.CLAIM_COUNTRIES_WITH_100_YEARS_PMA_OR_SHORTER
        if years_since_death > 80:
            return self._public_domain_claims.CLAIM_COUNTRIES_WITH_80_YEARS_PMA_OR_SHORTER
        if years_since_death > 70:
            return self._public_domain_claims.CLAIM_COUNTRIES_WITH_70_YEARS_PMA_OR_SHORTER
        if years_since_death > 50:
            return self._public_domain_claims.CLAIM_COUNTRIES_WITH_50_YEARS_PMA_OR_SHORTER
        return None
