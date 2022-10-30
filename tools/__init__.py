import re

from pywikibot import Site, Page


class ToolException(Exception):
    pass


def fetch_text_from_wiki_site(wiki: Site, lemma: str) -> str:  # pragma: no cover
    text: str = Page(wiki, lemma).text
    if not text:
        raise ToolException(f"The lemma {lemma} is empty.")
    return text


def save_if_changed(page: Page, text: str, change_msg: str):
    if text.rstrip() != page.text:
        page.text = text
        page.save(change_msg, botflag=True)


def add_category(text: str, category: str) -> str:
    if not re.search(rf"\[\[Kategorie:{category}", text):
        return text + f"\n[[Kategorie:{category}]]"
    return text
