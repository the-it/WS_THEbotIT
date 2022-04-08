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


LemmaDictKeys = Literal["lemma", "previous", "next", "sort_key", "redirect", "proof_read", "short_description",
                        "wp_link", "ws_link", "wd_link", "no_creative_height", "chapters"]
LemmaDictItems = Union[str, bool, int, List[ChapterDict]]


class LemmaDict(TypedDict, total=False):
    lemma: str
    previous: str
    next: str
    sort_key: str
    redirect: Union[str, bool]
    proof_read: int
    short_description: str
    wp_link: str
    ws_link: str
    wd_link: str
    no_creative_height: bool
    chapters: List[ChapterDict]


UpdaterRemoveList = List[str]
