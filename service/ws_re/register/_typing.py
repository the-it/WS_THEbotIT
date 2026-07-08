from typing import TypedDict, Dict, List, Union


class AuthorDict(TypedDict, total=False):
    birth: int
    death: int
    first_name: str
    last_name: str
    wp_lemma: str
    ws_lemma: str
    redirect: str


CrawlerDict = Dict[str, Union[str, List[str], Dict[str, str]]]
