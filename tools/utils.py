import pywikibot


def _has_category(lemma: pywikibot.Page, category_to_find: str) -> bool:
    categories: list[str] = [category.title() for category in lemma.categories()]
    category_found = False
    for category in categories:
        if not category.find(category_to_find) < 0:
            category_found = True
            break
    return category_found

def has_fertig_category(lemma: pywikibot.Page) -> bool:
    return _has_category(lemma, 'Fertig')

def has_korrigiert_category(lemma: pywikibot.Page) -> bool:
    return _has_category(lemma, 'Korrigiert')
