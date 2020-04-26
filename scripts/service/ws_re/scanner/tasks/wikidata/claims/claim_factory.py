import re
from abc import abstractmethod
from typing import Dict, List, Tuple, TypedDict, Union

import pywikibot

from scripts.service.ws_re.register.author import Author
from scripts.service.ws_re.register.authors import Authors
from scripts.service.ws_re.template.article import Article
from scripts.service.ws_re.template.re_page import RePage
# type hints
from scripts.service.ws_re.volumes import Volume, Volumes
from tools.bots import BotException

ClaimList = List[pywikibot.Claim]
ClaimDictionary = Dict[str, ClaimList]
SerializedClaimList = List[Dict]
SerializedClaimDictionary = Dict[str, SerializedClaimList]


class ChangedClaimsDict(TypedDict):
    add: ClaimDictionary
    remove: ClaimList


JsonValueDict = TypedDict('JsonValueDict', {'entity-type': str, 'numeric-id': int})


class JsonDataValue(TypedDict):
    value: Union[str, JsonValueDict]
    type: str


class JsonSnakDict(TypedDict):
    snaktype: str
    property: str
    datatype: str
    datavalue: JsonDataValue


class JsonClaimDict(TypedDict):
    mainsnak: JsonSnakDict
    type: str
    rank: str


class ClaimFactory:
    _authors = Authors()
    _volumes = Volumes()

    def __init__(self, re_page: RePage):
        self.wikidata = re_page.page.data_repository
        self.wikisource = re_page.page.site
        self.re_page = re_page

    @abstractmethod
    def _get_claim_json(self) -> JsonClaimDict:
        """

        """
        pass

    def get_claims_to_update(self, data_item: pywikibot.ItemPage) -> ChangedClaimsDict:
        """
        Every claim that is updated can possible add new claims, but can also remove existing claims at the item.
        Which claims is removed or added depends of the specific implementation of the property factory. The standart
        implementation will update all claims as expected by the factory (this include removing possible existing
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
        return re.search(r"^P\d{1,6}", cls.__name__).group(0)

    @property
    def _first_article(self) -> Article:
        """
        Holds the first article of the RE lemma to analyse
        """
        return self.re_page[0]

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

    def get_diff_claims_for_replacement(self, claim_list: ClaimList, data_item: pywikibot.ItemPage) -> ClaimDictionary:
        try:
            old_claims = data_item.claims[self.get_property_string()]
        except KeyError:
            old_claims = []
        claims_to_add, claims_to_remove = self._filter_new_vs_old_claim_list(claim_list, old_claims)
        return self._create_claim_dictionary(claims_to_add, claims_to_remove)

    @staticmethod
    def create_claim_json(property_str: str, target_type: str, target: str) -> JsonClaimDict:
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

    def _authors_of_first_article(self) -> List[Author]:
        author_list: List[Author] = []
        for article_part in self.re_page.splitted_article_list[0]:
            if isinstance(article_part, str):
                continue
            author = article_part.author[0]
            band = self.re_page[0]["BAND"].value
            possible_authors = self._authors.get_author_by_mapping(author, band)
            if len(possible_authors) == 1:
                author_list.append(possible_authors[0])
        return author_list

    @property
    def _volume_of_first_article(self) -> Volume:
        return self._volumes[str(self._first_article["BAND"].value)]
