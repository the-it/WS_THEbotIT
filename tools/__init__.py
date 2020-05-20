import os

from pywikibot import Site, Page


class ToolException(Exception):
    pass


def make_html_color(min_value, max_value, value):
    if max_value >= min_value:
        color = (1 - (value - min_value) / (max_value - min_value)) * 255
    else:
        color = ((value - max_value) / (min_value - max_value)) * 255
    color = max(0, min(255, color))
    return str(hex(round(color)))[2:].zfill(2).upper()


def fetch_text_from_wiki_site(wiki: Site, lemma: str) -> str:  # pragma: no cover
    text: str = Page(wiki, lemma).text
    if not text:
        raise ToolException(f"The lemma {lemma} is empty.")
    return text


REAL_DATA_TEST = "WS_REAL_DATA" in os.environ
REAL_WIKI_TEST = "WS_REAL_WIKI" in os.environ
