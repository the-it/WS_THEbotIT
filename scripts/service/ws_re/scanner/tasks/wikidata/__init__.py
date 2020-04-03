import json
import re
from pathlib import Path
from string import Template
from typing import Dict, Callable, List

import dictdiffer
import pywikibot

from scripts.service.ws_re.register.authors import Authors
from scripts.service.ws_re.scanner import ReScannerTask
from scripts.service.ws_re.template.article import Article
from scripts.service.ws_re.volumes import Volumes
from tools.bots.pi import WikiLogger


class DATATask(ReScannerTask):
    _languages = ("de", "en", "fr", "nl")

    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        ReScannerTask.__init__(self, wiki, logger, debug)
        self.wikidata: pywikibot.Site = pywikibot.Site(code="wikidata", fam="wikidata", user="THEbotIT")
        with open(Path(__file__).parent.joinpath("non_claims.json")) as non_claims_json:
            self._non_claims_template = Template(non_claims_json.read())
        self._claim_functions = self._get_claim_functions()
        self._authors = Authors()
        self._first_article: Article
        self._volumes = Volumes()

    def task(self):
        self._first_article = self.re_page[0]
        try:
            # edit existing wikidata item
            #######################################
            self.p155()
            self.p156()
            #############################
            return True
            data_item: pywikibot.ItemPage = self.re_page.page.data_item()
            data_item.get()
            self._update_non_claims(data_item)
            self._update_claims(data_item)
        except pywikibot.NoPage:
            # create a new one from scratch
            data_item: pywikibot.ItemPage = self.wikidata.createNewItemFromPage(page=self.re_page.page)

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
        returns a claim must be names as _pXXXX.
        """
        claim_functions = {}
        for item in dir(self):
            if re.search(r"^p\d{1,6}", item):
                claim_functions[item.upper()] = getattr(self, item)
        return claim_functions

    def _update_claims(self, data_item: pywikibot.ItemPage):
        claims_to_add: Dict[str, List[pywikibot.Claim]] = {}
        claims_to_remove: List[pywikibot.Claim] = []
        for claim_str, claim_function in self._claim_functions.items():
            new_claim_list = claim_function()
            old_claim_list = data_item.claims[claim_str]
            if self._claim_list_has_changed(new_claim_list, old_claim_list):
                claims_to_add[claim_str] = new_claim_list
                claims_to_remove += old_claim_list
        data_item.removeClaims(claims_to_remove)
        data_item.editEntity({"claims": claims_to_add})
        print(data_item.toJSON())

    def _claim_list_has_changed(self, new_claim_list: List[pywikibot.Claim],
                                old_claim_list: List[pywikibot.Claim]) -> bool:
        new_processed_claim_list = self._preprocess_claim_list(new_claim_list)
        old_processed_claim_list = self._preprocess_claim_list(old_claim_list)
        return bool(tuple(dictdiffer.diff(new_processed_claim_list, old_processed_claim_list)))

    def _preprocess_claim_list(self, claim_list: List[pywikibot.Claim]) -> List[Dict]:
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
            claim = pywikibot.Claim(self.wikidata, 'P31')
            claim.setTarget(author)
            claim_list.append(claim)
        return claim_list

    def _p50_get_author_list(self) -> List[pywikibot.Claim]:
        author_items: List[pywikibot.Claim] = []
        for article_part in self.re_page.splitted_article_list[0]:
            author = article_part.author[0]
            band = self._first_article["BAND"].value
            author_list = self._authors.get_author_by_mapping(author, band)
            if len(author_list) == 1:
                author_lemma = pywikibot.Page(self.wiki, author_list[0].name)
                if not author_lemma.exists():
                    continue
                try:
                    # append the item of the author, if it exists
                    author_items.append(author_lemma.data_item())
                except pywikibot.NoPage:
                    continue
        return author_items

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
        publication_year = self._get_publication_year()
        claim = pywikibot.Claim(self.wikidata, 'P577')
        claim.setTarget(pywikibot.WbTime(year=publication_year))
        return [claim]

    def _get_publication_year(self):
        return int(self._volumes[self._first_article["BAND"].value].year)

    def p921(self) -> List[pywikibot.Claim]:
        """
        Returns the Claim **main subject** -> **<Item of wikipedia article>**
        """
        wp_article = self._first_article["WIKIPEDIA"].value
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
