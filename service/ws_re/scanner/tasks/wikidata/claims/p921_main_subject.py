from typing import Dict, List, Optional

import pywikibot
from pywikibot.data import sparql

from service.ws_re.scanner.tasks.wikidata.claims._base import SnakParameter
from service.ws_re.scanner.tasks.wikidata.claims._typing import ChangedClaimsDict, JsonClaimDict
from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory


class P921MainSubject(ClaimFactory):
    """
    Returns the Claim **main subject** -> **<Item of wikipedia article>**

    If no wikipedia article is linked, fall back to items that already point to the
    RE article via **described by source** (P1343) -> RE with the qualifier
    **section, verse, paragraph, or clause** (P958) -> <lemma>.
    """

    ERROR_CAT = "RE:Wartung Wikidata (WD!=WS)"

    _BACKLINK_QUERY = """SELECT ?candidate ?REArticle WHERE {
  ?candidate p:P1343 ?st.
  ?st ps:P1343 wd:Q1138524;
    pq:P958 ?REArticle.
}"""
    # lazy initialized mapping <lemma without prefix> -> <item id>, shared by all instances
    _backlink_mapping: Optional[Dict[str, str]] = None

    def _get_claim_json(self) -> List[JsonClaimDict]:
        target_item_id = self._get_item_of_wp_article()
        if not target_item_id:
            target_item_id = self.get_backlink_mapping().get(self.re_page.lemma_without_prefix)
        # if no target was found, there is nothing to connect
        if not target_item_id:
            return []
        # finally create the claim
        snak = SnakParameter(property_str=self.get_property_string(),
                             target_type="wikibase-item",
                             target=target_item_id)

        return [self.create_claim_json(snak, references=[[self._IMPORTED_FROM_WIKISOURCE]])]

    def _get_item_of_wp_article(self) -> Optional[str]:
        wp_article = str(self.re_page.first_article["WIKIPEDIA"].value)
        # if no wp_article is present, there is nothing to connect
        if not wp_article:
            return None
        # handle the case of an implicit de:
        if ":" not in wp_article:
            wp_article = f"de:{wp_article}"
        language, wp_page_str = wp_article.split(":")
        wp_site: pywikibot.Site = pywikibot.Site(code=language, fam="wikipedia")
        wp_page: pywikibot.Page = pywikibot.Page(wp_site, wp_page_str)
        # try to fetch the data item of the page, if not there is nothing to connect
        try:
            wp_data_item: pywikibot.ItemPage = wp_page.data_item()
        except (pywikibot.exceptions.NoPageError, pywikibot.exceptions.InvalidTitleError):
            return None
        return str(wp_data_item.id)

    @classmethod
    def get_backlink_mapping(cls) -> Dict[str, str]:
        if cls._backlink_mapping is None:
            query_result = sparql.SparqlQuery().select(cls._BACKLINK_QUERY)
            cls._backlink_mapping = cls._process_backlink_query(query_result or [])
        return cls._backlink_mapping

    @staticmethod
    def _process_backlink_query(query_result: List[Dict[str, str]]) -> Dict[str, str]:
        mapping: Dict[str, str] = {}
        ambiguous_lemmas = set()
        for row in query_result:
            lemma = row["REArticle"]
            item_id = row["candidate"].rsplit("/", maxsplit=1)[-1]
            # if two different items claim the same RE article, no clear target exists
            if lemma in mapping and mapping[lemma] != item_id:
                ambiguous_lemmas.add(lemma)
            mapping[lemma] = item_id
        for lemma in ambiguous_lemmas:
            del mapping[lemma]
        return mapping

    def get_claims_to_update(self, data_item: pywikibot.ItemPage) -> ChangedClaimsDict:
        """
        Only add claims, if no claim already exist.
        Alert with an error if existing claim and added claim are different.

        :param: data_item: item where the specific property is going to be altered

        :returns: A dictionary with claims to add and to remove is returned
        """
        claim_json = self._get_claim_json()
        if not claim_json:
            return self._create_claim_dictionary([], [])
        new_claim: pywikibot.Claim = pywikibot.Claim.fromJSON(self.wikidata, claim_json[0])
        old_claims = self.get_old_claims(data_item)
        # no old claim exists yet
        if not old_claims:
            return self._create_claim_dictionary([new_claim], [])
        # if the existing claim is a redirect, replace it
        if old_claims[0].target.isRedirectPage():
            return self._create_claim_dictionary([self.replace_redirect(old_claims[0])],
                                                 [old_claims[0]])
        if not new_claim.same_as(old_claims[0]):
            self.re_page.add_error_category(self.ERROR_CAT)
        else:
            self.re_page.remove_error_category(self.ERROR_CAT)
        return self._create_claim_dictionary([], [])

    @staticmethod
    def replace_redirect(old_claim: pywikibot.Claim) -> pywikibot.Claim:
        new_claim = old_claim.copy()
        new_claim.setTarget(old_claim.target.getRedirectTarget())
        return new_claim
