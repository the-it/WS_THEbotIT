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
        page.save(change_msg, bot=True)


def add_category(text: str, category: str) -> str:
    if not re.search(rf"\[\[Kategorie:{category}", text):
        return text + f"\n[[Kategorie:{category}]]"
    return text


def _has_category(lemma: Page, category_to_find: str) -> bool:
    categories: list[str] = [category.title() for category in lemma.categories()]
    category_found = False
    for category in categories:
        if not category.find(category_to_find) < 0:
            category_found = True
            break
    return category_found


def has_fertig_category(lemma: Page) -> bool:
    return _has_category(lemma, 'Fertig')


def has_korrigiert_category(lemma: Page) -> bool:
    return _has_category(lemma, 'Korrigiert')
