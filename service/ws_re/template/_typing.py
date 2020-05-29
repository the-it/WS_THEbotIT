from typing import TypedDict, Dict, Union

PropertyValueType = Union[str, bool]
ArticleProperties = Dict[str, PropertyValueType]


class KeyValuePair(TypedDict):
    key: str
    value: PropertyValueType
