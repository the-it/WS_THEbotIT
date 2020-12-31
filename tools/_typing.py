from typing import TypedDict, Tuple, Optional, List


class TemplatePositionDict(TypedDict):
    pos: Tuple[int, int]
    text: str


class TemplateParameterDict(TypedDict):
    key: Optional[str]
    value: str


TemplateParameterList = List[TemplateParameterDict]


class PetscanLemma(TypedDict):
    id: int
    len: int
    n: str
    namespace: int
    nstext: str
    title: str
    touched: str
