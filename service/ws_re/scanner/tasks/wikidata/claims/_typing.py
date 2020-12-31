from typing import List, Dict, TypedDict, Union, Optional

import pywikibot

ClaimList = List[pywikibot.Claim]
ClaimDictionary = Dict[str, ClaimList]


class ChangedClaimsDict(TypedDict):
    add: ClaimDictionary
    remove: ClaimList


JsonValueDictItem = TypedDict("JsonValueDictItem", {"entity-type": str, "numeric-id": int})
JsonValueDictTime = TypedDict("JsonValueDictTime", {"time": str,
                                                    "precision": int,
                                                    "after": int,
                                                    "before": int,
                                                    "timezone": int,
                                                    "calendarmodel": str})
JsonValueDictMonolingualtext = TypedDict("JsonValueDictMonolingualtext", {"text": str, "language": str})


class JsonDataValue(TypedDict):
    value: Union[str, JsonValueDictItem, JsonValueDictTime, JsonValueDictMonolingualtext]
    type: str


class JsonSnakDict(TypedDict):
    snaktype: str
    property: str
    datatype: str
    datavalue: JsonDataValue


ReferencesList = List[Dict[str, Optional[Union[List[str], Dict[str, List[JsonSnakDict]]]]]]
JsonClaimDict = TypedDict("JsonClaimDict",
                          {"mainsnak": JsonSnakDict,
                           "type": str,
                           "rank": str,
                           "qualifiers": Dict[str, List[JsonSnakDict]],
                           "qualifiers-order": List[str],
                           "references": ReferencesList
                           },
                          total=False)
