import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional

import pywikibot

from service.ws_re.register.author import Author
from service.ws_re.register.authors import Authors
from service.ws_re.scanner.tasks.wikidata.claims._base import SnakParameter
from service.ws_re.scanner.tasks.wikidata.claims._typing import ClaimList, ChangedClaimsDict, JsonDataValue, \
    JsonSnakDict, ReferencesList, JsonClaimDict
from service.ws_re.template.article import Article
from service.ws_re.template.re_page import RePage, ArticleList
from service.ws_re.volumes import Volume, Volumes
from tools.bots import BotException
from tools.bots.logger import WikiLogger


class ClaimFactory:
    _authors = Authors()
    _volumes = Volumes()
    ITEM_RE = "Q1138524"
    _IMPORTED_FROM_WIKISOURCE = SnakParameter(property_str="P143",
                                              target_type="wikibase-item",
                                              target="Q15522295")

    def __init__(self, re_page: RePage, logger: WikiLogger):
        self.wikisource: pywikibot.Site = pywikibot.Site(code="de", fam="wikisource", user="THEbotIT")
        self.wikipedia: pywikibot.Site = pywikibot.Site(code="de", fam="wikipedia", user="THEbotIT")
        self.wikidata: pywikibot.site.DataSite = self.wikisource.data_repository()
        self.re_page = re_page
        self.logger = logger
        self._current_year = datetime.now().year

    def _get_claim_json(self) -> List[JsonClaimDict]:
        raise NotImplementedError

    def get_claims_to_update(self, data_item: pywikibot.ItemPage) -> ChangedClaimsDict:
        """
        Every claim that is updated can possibly add new claims, but can also remove existing claims at the item.
        Which claims is removed or added depends on the specific implementation of the property factory. The standard
        implementation will update all claims as expected by the factory (this includes removing possible existing
        claims).

        :param: data_item: item where the specific property is going to be altered

        :returns: A dictionary with claims to add and to remove is returned
        """

        claim_list = [pywikibot.Claim.fromJSON(self.wikidata, claim_json)
                      for claim_json in self._get_claim_json()]
        return self.get_diff_claims_for_replacement(claim_list, data_item)

    @classmethod
    def get_property_string(cls) -> str:
        """
        Returns the property string for this class
        """
        if regex_hit := re.search(r"^P\d{1,6}", cls.__name__):
            return regex_hit.group(0)
        raise ValueError("Class name doesn't match regex")

    @classmethod
    def filter_new_vs_old_claim_list(cls,
                                     new_claim_list: ClaimList,
                                     old_claim_list: ClaimList) -> Tuple[ClaimList, ClaimList]:
        """
        If desired that the updated claims must exactly match the new_claim_list,
        this function searches throw the existing claims and the desired state. It only returns the claims that must
        added or removed from the item.

        **Examples**:

        new_claim_list, old_claim_list -> filtered_new_claim_list, filtered_old_claim_list

        * [A, B, C], [B, D] -> [A, C], [D]
        * [A], [] -> [A], []
        * [], [A] -> [], [A]
        * [A,B,C], [A,B,C] -> [], []

        :param new_claim_list: calculated desired state of the claims
        :param old_claim_list: present state of the claims at the item
        :return: Tuple of two claim lists, first is the new claims that must added,
                 the second list represents the claims that are destined to be removed.
        """
        filtered_new_claim_list = []
        for new_claim in new_claim_list:
            for old_claim in old_claim_list:
                if new_claim.same_as(old_claim):
                    old_claim_list.remove(old_claim)
                    break
            else:
                # not match found, no old claim matches this new one
                filtered_new_claim_list.append(new_claim)
        return filtered_new_claim_list, old_claim_list

    def _create_claim_dictionary(self, claims_to_add: ClaimList, claims_to_remove: ClaimList) -> ChangedClaimsDict:
        claims_to_add_dict = {}
        if claims_to_add:
            claims_to_add_dict[self.get_property_string()] = claims_to_add
        return {"add": claims_to_add_dict, "remove": claims_to_remove}

    def get_diff_claims_for_replacement(self,
                                        claim_list: ClaimList,
                                        data_item: pywikibot.ItemPage) -> ChangedClaimsDict:
        old_claims = self.get_old_claims(data_item)
        claims_to_add, claims_to_remove = self.filter_new_vs_old_claim_list(claim_list, old_claims)
        return self._create_claim_dictionary(claims_to_add, claims_to_remove)

    def get_old_claims(self, data_item) -> List[pywikibot.Claim]:
        try:
            old_claims: List[pywikibot.Claim] = data_item.claims[self.get_property_string()]
        except (AttributeError, KeyError):
            # if data_item didn't existed -> AttributeError, if claim not exists -> KeyError
            old_claims = []
        return old_claims

    @staticmethod
    def create_claim_json(snak_parameter: SnakParameter,
                          qualifiers: Optional[List[SnakParameter]] = None,
                          references: Optional[List[List[SnakParameter]]] = None) -> JsonClaimDict:
        """
        This factory function create json representations of claims from some basic parameters.

        :param snak_parameter: parameters for the actual claim
        :param qualifiers: optional parameters for qualifiers
        :param references: optional parameters for references

        :return: dictionary representation of a claim
        """
        snak = ClaimFactory.create_snak_json(snak_parameter)
        claim_json: JsonClaimDict = {"mainsnak": snak,
                                     "type": "statement",
                                     "rank": "normal"}
        if qualifiers:
            qualifiers_dict, qualifiers_order_list = ClaimFactory._add_qualifiers(qualifiers)
            claim_json["qualifiers"] = qualifiers_dict
            claim_json["qualifiers-order"] = qualifiers_order_list
        if references:
            references_list = ClaimFactory._add_references(references)
            claim_json["references"] = references_list
        return claim_json

    @staticmethod
    def _add_references(references) -> ReferencesList:
        references_snak: ReferencesList = []
        for reference_list in references:
            reference_list_snak = {}
            reference_list_snak_order = []
            for reference in reference_list:
                reference_list_snak[reference.property_str] = [ClaimFactory.create_snak_json(reference)]
                reference_list_snak_order.append(reference.property_str)
            references_snak.append({"snaks": reference_list_snak, "snaks-order": reference_list_snak_order})
        return references_snak

    @staticmethod
    def _add_qualifiers(qualifiers: List[SnakParameter]) -> Tuple[Dict[str, List[JsonSnakDict]], List[str]]:
        qualifiers_dict = {}
        qualifiers_order_list = []
        for qualifier in qualifiers:
            qualifier_snak = ClaimFactory.create_snak_json(qualifier)
            if qualifier.property_str not in qualifiers_dict:
                qualifiers_dict[qualifier.property_str] = [qualifier_snak]
            else:
                qualifiers_dict[qualifier.property_str].append(qualifier_snak)
            if qualifier.property_str not in qualifiers_order_list:
                qualifiers_order_list.append(qualifier.property_str)
        return qualifiers_dict, qualifiers_order_list

    @staticmethod
    def create_snak_json(snak_parameter: SnakParameter) -> JsonSnakDict:
        datavalue: JsonDataValue
        if snak_parameter.target_type == "wikibase-item":
            datavalue = {"value": {"entity-type": "item",
                                   "numeric-id": int(snak_parameter.target.strip("Q"))
                                   },
                         "type": "wikibase-entityid"
                         }
        elif snak_parameter.target_type == "string":
            datavalue = {"value": snak_parameter.target,
                         "type": "string"
                         }
        elif snak_parameter.target_type == "time":
            # only for years at the moment ... extend if necessary
            datavalue = {"value": {"time": f"+0000000{int(snak_parameter.target)}-01-01T00:00:00Z",
                                   "precision": 9,
                                   "after": 0,
                                   "before": 0,
                                   "timezone": 0,
                                   "calendarmodel": "http://www.wikidata.org/entity/Q1985727"
                                   },
                         "type": "time"
                         }
        elif snak_parameter.target_type == "monolingualtext":
            datavalue = {"value": {"text": snak_parameter.target,
                                   "language": "mul"
                                   },
                         "type": "monolingualtext"
                         }
        else:
            raise BotException(f"target_type \"{snak_parameter.target_type}\" not supported")
        return {"snaktype": "value",
                "property": snak_parameter.property_str,
                "datatype": snak_parameter.target_type,
                "datavalue": datavalue}

    # CLAIM FUNCTIONS THAT ARE NEEDED FOR MULTIPLE CLAIM FACTORIES

    def get_authors_article(self, article_list: ArticleList) -> List[Author]:
        author_list: List[Author] = []
        for article_part in article_list:
            author = article_part.author.identification
            band = article_list[0]["BAND"].value
            possible_authors = self._authors.get_author_by_mapping(author, band)
            if len(possible_authors) == 1:
                author_list.append(possible_authors[0])
        return author_list

    def _volume_of_article(self, article: Article) -> Volume:
        return self._volumes[str(article["BAND"].value)]
