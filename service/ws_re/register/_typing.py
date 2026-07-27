from typing import TypedDict


class AuthorDict(TypedDict, total=False):
    birth: int
    death: int
    first_name: str
    last_name: str
    wp_lemma: str
    ws_lemma: str
    redirect: str


CrawlerDict = dict[str, str | list[str] | dict[str, str]]
