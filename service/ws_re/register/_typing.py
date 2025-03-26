from typing import TypedDict, Dict, Union


class AuthorDict(TypedDict, total=False):
    birth: int
    death: int
    first_name: str
    last_name: str
    wp_lemma: str
    ws_lemma: str
    redirect: str


CrawlerDict = Dict[str, Union[str, Dict[str, str]]]
