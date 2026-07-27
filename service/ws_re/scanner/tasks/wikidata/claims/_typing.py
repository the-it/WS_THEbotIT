from typing import TypedDict

import pywikibot

ClaimList = list[pywikibot.Claim]
ClaimDictionary = dict[str, ClaimList]


class ChangedClaimsDict(TypedDict):
    add: ClaimDictionary
    remove: ClaimList


JsonValueDictItem = TypedDict("JsonValueDictItem", {"entity-type": str, "numeric-id": int})
JsonValueDictTime = TypedDict(
    "JsonValueDictTime",
    {"time": str, "precision": int, "after": int, "before": int, "timezone": int, "calendarmodel": str},
)
JsonValueDictMonolingualtext = TypedDict("JsonValueDictMonolingualtext", {"text": str, "language": str})


class JsonDataValue(TypedDict):
    value: str | JsonValueDictItem | JsonValueDictTime | JsonValueDictMonolingualtext
    type: str


class JsonSnakDict(TypedDict):
    snaktype: str
    property: str
    datatype: str
    datavalue: JsonDataValue


ReferencesList = list[dict[str, list[str] | dict[str, list[JsonSnakDict]] | None]]
JsonClaimDict = TypedDict(
    "JsonClaimDict",
    {
        "mainsnak": JsonSnakDict,
        "type": str,
        "rank": str,
        "qualifiers": dict[str, list[JsonSnakDict]],
        "qualifiers-order": list[str],
        "references": ReferencesList,
    },
    total=False,
)
