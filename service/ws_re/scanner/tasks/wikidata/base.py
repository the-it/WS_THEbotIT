from service.ws_re.template.re_page import RePage


def get_article_type(re_page: RePage) -> str:
    INDEX_LIST = (
        "Register (Band XI)",
        "Mitarbeiter-Verzeichnis (Band II)",
        "Verzeichnis der Mitarbeiter nach dem Stand vom 1. Mai 1913",
    )
    PROLOGUE_LIST = (
        "Abkürzungen",
        "Abkürzungen (Supplementband I)",
        "Vorwort (Band I)",
        "Vorwort (Supplementband I)",
        "Wilhelm Kroll †",
    )
    if re_page.lemma_without_prefix in INDEX_LIST:
        return "index"
    if re_page.lemma_without_prefix in PROLOGUE_LIST:
        return "prologue"
    if re_page[0]["VERWEIS"].value:
        return "crossref"
    return "article"
