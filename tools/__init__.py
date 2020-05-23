from pywikibot import Site, Page


class ToolException(Exception):
    pass


def fetch_text_from_wiki_site(wiki: Site, lemma: str) -> str:  # pragma: no cover
    text: str = Page(wiki, lemma).text
    if not text:
        raise ToolException(f"The lemma {lemma} is empty.")
    return text
