from typing import TypedDict, Dict, Union, Literal, List


class AuthorDict(TypedDict, total=False):
    birth: int
    death: int
    first_name: str
    last_name: str
    wp_lemma: str
    ws_lemma: str
    redirect: str


CrawlerDict = Dict[str, Union[str, Dict[str, str]]]


class ChapterDict(TypedDict, total=False):
    author: str
    start: int
    end: int


LemmaDictKeys = Literal["lemma", "previous", "next", "sort_key", "redirect",
                        "proof_read", "wp_link", "ws_link", "wd_link", "chapters"]
LemmaDictItems = Union[str, bool, int, List[ChapterDict]]


class LemmaDict(TypedDict, total=False):
    lemma: str
    previous: str
    next: str
    sort_key: str
    redirect: Union[str, bool]
    proof_read: int
    wp_link: str
    ws_link: str
    wd_link: str
    chapters: List[ChapterDict]


UpdaterRemoveList = List[str]
