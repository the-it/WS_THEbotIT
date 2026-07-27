from typing import TypedDict


class TemplateParameterDict(TypedDict):
    key: str | None
    value: str


TemplateParameterList = list[TemplateParameterDict]


class PetscanLemma(TypedDict):
    id: int
    len: int
    n: str
    namespace: int
    nstext: str
    title: str
    touched: str
