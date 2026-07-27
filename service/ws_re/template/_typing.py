from typing import TypedDict

PropertyValueType = str | bool
ArticleProperties = dict[str, PropertyValueType]


class KeyValuePair(TypedDict):
    key: str
    value: PropertyValueType
