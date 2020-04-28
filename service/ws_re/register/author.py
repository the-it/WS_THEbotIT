from typing import Dict, Union, Optional, TypedDict


# type hints
class AuthorDict(TypedDict, total=False):
    birth: int
    death: int
    first_name: str
    last_name: str
    redirect: str


CrawlerDict = Dict[str, Union[str, Dict[str, str]]]


class Author:
    def __init__(self, name: str, author_dict: AuthorDict):
        self._dict = author_dict
        if "_" in name:
            name = name.split("_")[0]
        self._name = name

    def __repr__(self):  # pragma: no cover
        return f"<{self.__class__.__name__} - name:{self.name}, birth:{self.birth}, death:{self.death}>"

    @property
    def death(self) -> Optional[int]:
        if "death" in self._dict.keys():
            return self._dict["death"]
        return None

    @property
    def birth(self) -> Optional[int]:
        if "birth" in self._dict.keys():
            return self._dict["birth"]
        return None

    @property
    def first_name(self) -> Optional[str]:
        if "first_name" in self._dict.keys():
            return self._dict["first_name"]
        return None

    @property
    def last_name(self) -> str:
        if "last_name" in self._dict.keys():
            return self._dict["last_name"]
        return ""

    @property
    def redirect(self) -> Optional[str]:
        if "redirect" in self._dict.keys():
            return self._dict["redirect"]
        return None

    @property
    def name(self) -> str:
        return self._name

    def update_internal_dict(self, author_dict: AuthorDict):
        self._dict.update(author_dict)

    def to_dict(self) -> AuthorDict:
        return self._dict
