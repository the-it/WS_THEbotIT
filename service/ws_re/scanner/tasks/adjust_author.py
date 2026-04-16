import re

import pywikibot

from service.ws_re.register.authors import Authors
from service.ws_re.scanner.tasks.base_task import ReScannerTask
from service.ws_re.template.article import Article
from tools.bots.logger import WikiLogger

ADDITIONAL_AUTHORS: dict[str, str] = {
    "Franz Heinrich Weissbach": "Weissbach.",
    "Hans von Arnim": "v. Arnim.",
    "Paul Friedländer": "P. Friedländer.",
    "Felix Jacoby": "F. Jacoby.",
    "Hans von Geisau": "v. Geisau.",
    "Paul Schoch-Bodmer": "Schoch.",
    "Max Fluß": "Fluss.",
    "August Burckhardt-Brandenberg": "Burckhardt.",
    "Johannes Geffcken": "Geffcken.",
    "Walther Eltester": "Eltester.",
    "Fritz Geyer": "Geyer.",
    "Bernhard große Kruse": "gr. Kruse.",
    "Wilhelm Enßlin": "W. Enßlin.",
    "Walter Friedrich Otto": "W. F. Otto.",
    "Hans Philipp": "Philipp.",
    "Schmidt": "Johanna Schmidt.",
    "Albert William Van Buren": "A. W. Van Buren.",
    "Judith Andrée-Hanslik": "Judith Andrée-Hanslik.",
    "Anthony Eric Raubitschek": "A. Raubitschek.",
    "Hans Georg Gundel": "H. Gundel.",
    "Max Lambertz": "Lambertz.",
    "Karl Wolf": "Wolf.",
}

COMPLEX_AUTHORS: dict[str, str] = {
    "Ernst Hugo Berger": "Berger.",
    "Adolf Berger": "Berger.",
    "Ludo Moritz Hartmann": "Hartmann.",
    "Richard Hartmann": "Hartmann.",
    "Maria Assunta Nagl": "Nagl.",
    "Alfred Nagl": "Nagl.",
    "Alfred Philippson": "Philippson.",
    "Johannes Schmidt (Epigraphiker)": "J. Schmidt.",
    "Johannes Schmidt (Philologe)": "J. Schmidt.",
    "Ernst Schwabe": "Schwabe.",
    "Ludwig Schwabe": "Schwabe.",
    "Hans Schaefer": "Hans Schaefer.",
}

REGEX_COMPLEX = re.compile(rf"REAutor\|(?P<author>{'|'.join(set(COMPLEX_AUTHORS.values()))})")


def get_author_mapping() -> dict[str, str]:
    authors = Authors()
    author_raw_mapping: dict[str, list[str]] = {}
    for author in authors.authors_mapping:
        if isinstance(authors.authors_mapping[author], (dict, list)):
            continue
        if authors.authors_mapping[author] not in author_raw_mapping:
            author_raw_mapping[authors.authors_mapping[author]] = []
        author_raw_mapping[authors.authors_mapping[author]].append(author)
    author_mapping = {}
    for key, value in author_raw_mapping.items():
        value = [item for item in value if item[-1] == "."]
        if len(value) == 1 and value[0][-1] == ".":
            author_mapping[key] = value[0]
        else:
            last_name = f"{key.split(" ")[-1]}."
            name_list = []
            for name in key.split(" ")[0:-1]:
                name_list.append(f"{name[0]}.")
            name_list.append(last_name)
            long_last_name = " ".join(name_list)
            if last_name in value:
                author_mapping[key] = last_name
            elif long_last_name in value:
                author_mapping[key] = long_last_name

    author_mapping.update(ADDITIONAL_AUTHORS)
    author_mapping.update(COMPLEX_AUTHORS)
    return author_mapping


def adjust_author(input_str: str, mapping: dict[str, str]) -> str:
    for author in mapping:
        input_str = re.sub(rf"{{{{REAutor\|{author}}}}}",
                           f"{{{{REAutor|{mapping[author]}}}}}",
                           input_str)
    if REGEX_COMPLEX.search(input_str):
        article = Article.from_text(input_str.strip())
        input_str = REGEX_COMPLEX.sub(rf"REAutor|\g<author>|{article["BAND"].value}", input_str)
    return input_str


class ADAUTask(ReScannerTask):
    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        self.author_mapping = get_author_mapping()
        self.complex_short_names = set(COMPLEX_AUTHORS.values())
        super().__init__(wiki, logger, debug)

    def task(self) -> bool:
        for article in self.re_page:
            if not isinstance(article, Article):
                continue
            if str(article["KORREKTURSTAND"].value) != "unvollständig":
                continue
            author = article.author
            if author.short_string in self.author_mapping:
                author.short_string = self.author_mapping[author.short_string]
            if author.short_string in self.complex_short_names and not author.issue:
                author.issue = str(article["BAND"].value)
        return True
