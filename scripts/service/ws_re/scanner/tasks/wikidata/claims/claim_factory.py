import re
from abc import abstractmethod
from copy import deepcopy
from typing import Dict, List, Tuple, TypedDict

import pywikibot

from scripts.service.ws_re.register.author import Author
from scripts.service.ws_re.template.re_page import RePage

# type hints
from tools.bots import BotException

ClaimList = List[pywikibot.Claim]
ClaimDictionary = Dict[str, ClaimList]
SerializedClaimList = List[Dict]
SerializedClaimDictionary = Dict[str, SerializedClaimList]


class ChangedClaimsDict(TypedDict):
    add: ClaimDictionary
    remove: ClaimList


class ClaimFactory:
    def __init__(self, wikidata: pywikibot.Site):
        self.wikidata = wikidata

    @abstractmethod
    def get_claims_to_update(self, re_page: RePage, data_item: pywikibot.ItemPage) -> ChangedClaimsDict:
        """
        Every claim that is updated can possible add new claims, but can also remove existing claims at the item.
        Which claims is removed or added depends of the specific implementation of the property factory.

        :param: re_page: data representation of the RE lemma at wikisource
        :param: data_item: item where the specific property is going to be altered

        :returns: Two collections of claims are returned.
        """
        pass

    @classmethod
    def get_property_string(cls) -> str:
        """
        Returns the property string for this class
        """
        return re.search(r"^P\d{1,6}", cls.__name__).group(0)

    @staticmethod
    def _filter_new_vs_old_claim_list(new_claim_list: ClaimList, old_claim_list: ClaimList) \
        -> Tuple[ClaimList, ClaimList]:
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

    def _create_claim_dictionary(self, claims_to_add: ClaimList, claims_to_remove: ClaimList) -> ClaimDictionary:
        claims_to_add_dict = {}
        if claims_to_add:
            claims_to_add_dict[self.get_property_string()] = claims_to_add
        return {"add": claims_to_add_dict, "remove": claims_to_remove}

    def get_diff_claims_for_replacement(self, claim_list: ClaimList, data_item: pywikibot.ItemPage):
        old_claims = data_item.claims[self.get_property_string()]
        claims_to_add, claims_to_remove = self._filter_new_vs_old_claim_list(claim_list, old_claims)
        return self._create_claim_dictionary(claims_to_add, claims_to_remove)

    @staticmethod
    def create_claim_json(property_str: str, target_type: str, target: str) -> Dict:
        """
        This factory function create json representations of claims from some basic parameters.

        :param property_str: Number of the Property, example "P1234"
        :param target_type: Value of the target. Possible values: 'wikibase-item', 'string', 'commonsMedia',
                            'globe-coordinate', 'url', 'time', 'quantity', 'monolingualtext', 'math', 'external-id',
                            'geo-shape', 'tabular-data'
        :param target: actual value of the target
        :return: dictionary representation of a claim
        """
        claim_json: Dict = {'mainsnak': {'snaktype': 'value'},
                            'type': 'statement',
                            'rank': 'normal'}
        claim_json["mainsnak"]["property"] = property_str
        if target_type == "wikibase-item":
            claim_json["mainsnak"]["datatype"] = target_type
            claim_json["mainsnak"]["datavalue"] = {"value": {"entity-type": "item",
                                                             "numeric-id": int(target.strip("Q"))
                                                             },
                                                   "type": "wikibase-entityid"
                                                   }
        else:
            raise BotException(f"target_type \"{target_type}\" not supported")
        return claim_json

    # CLAIM FUNCTIONS THAT ARE NEEDED FOR MULTIPLE CLAIM FACTORIES

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
