import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from pywikibot import Site, Page, Category

from service.ws_re.register.authors import Authors
from service.ws_re.register.registers import Registers
from service.ws_re.template.article import Article
from tools import save_if_changed
from tools.bots.cloud_bot import CloudBot


class ReImporter(CloudBot):
    def __init__(self, wiki: Site = None, debug: bool = True,
                 log_to_screen: bool = True, log_to_wiki: bool = True):
        super().__init__(wiki, debug, log_to_screen, log_to_wiki)
        self.registers = Registers()
        self.new_articles: dict[str, dict[str, str]] = {}
        self.author_mapping = self.get_author_mapping()
        self.tm_set = self.load_tm_set()
        self._create_neuland()
        self.current_year = datetime.now().year
        self.max_create = min(75, 1000 - len(list(Category(self.wiki, "RE:Stammdaten überprüfen").articles())))

    def _create_neuland(self):
        for number in [1, 2, 3, 4, 5, 6, 7, 11, 12, 13]:
            neuland = Page(self.wiki, f"Wikisource:RE-Werkstatt/Neuland {number}")
            for raw in re.finditer(r"(\{\{REDaten.*?\{\{REAutor\|.*?\}\})\n\d{1,5}\s*„RE:(.*?)“", neuland.text,
                                   re.DOTALL):
                lemma = raw.group(2)
                article = raw.group(1)
                if match := re.search(r"BAND=(.{1,10})\n", article):
                    band = match.group(1)
                    if band not in self.new_articles:
                        self.new_articles[band] = {}
                    self.new_articles[band][lemma] = article

    @staticmethod
    def load_tm_set() -> set[str]:
        tm_set = set()
        file_path = Path(__file__).parent / "real_red_people.csv"
        with open(file_path, "r", encoding="utf-8") as file:
            for line in file.readlines():
                tm_set.add(line.strip().strip("\""))
        return tm_set

    def task(self):
        # pylint: disable=too-many-nested-blocks
        create_count = 0
        for register in self.registers.volumes.values():
            if create_count >= self.max_create:
                break
            for idx, article in enumerate(register):
                if article.proof_read is None:
                    # if article.get_public_domain_year() <= self.current_year:
                    # if article.lemma in self.tm_set:
                    lemma = Page(self.wiki, f"RE:{article.lemma}")
                    if not lemma.exists():
                        article_text = self.get_text(article.volume.name, article.lemma)
                        if article_text:
                            article_text = self.adjust_author(article_text, self.author_mapping)
                            article_text = self.adjust_end_column(article_text, register, idx)
                            article_text = (f"{article_text}\n[[Kategorie:RE:Stammdaten überprüfen]]"
                                            "\n[[Kategorie:RE:Kurztext überprüfen]]")
                            save_if_changed(lemma, article_text, "Automatisch generiert")
                            create_count += 1
                if create_count >= self.max_create:
                    self.logger.info(
                        f"Created {create_count} articles. Last article was [[RE:{article.lemma}]]"
                        f" in {register.volume.name}")
                    break
        return True

    def get_text(self, band: str, article: str) -> Optional[str]:
        band_dict = self.new_articles.get(band, None)
        if band_dict:
            article_text = band_dict.get(article, None)
            if article_text:
                return article_text
        return None

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
        "Ernst Schwabe": "J. Schwabe.",
        "Ludwig Schwabe": "J. Schwabe.",
    }

    REGEX_COMPLEX = re.compile(rf"REAutor\|(?P<author>{'|'.join(set(COMPLEX_AUTHORS.values()))})")

    @classmethod
    def get_author_mapping(cls) -> dict[str, str]:
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

        author_mapping.update(cls.ADDITIONAL_AUTHORS)
        author_mapping.update(cls.COMPLEX_AUTHORS)
        return author_mapping

    @classmethod
    def adjust_author(cls, input_str: str, mapping: dict[str, str]) -> str:
        for author in mapping:
            input_str = re.sub(rf"{{{{REAutor\|{author}}}}}",
                               f"{{{{REAutor|{mapping[author]}}}}}",
                               input_str)
        if cls.REGEX_COMPLEX.search(input_str):
            article = Article.from_text(input_str.strip())
            input_str = cls.REGEX_COMPLEX.sub(rf"REAutor|\g<author>|{article["BAND"].value}", input_str)
        return input_str

    @staticmethod
    def adjust_end_column(article_text, register, idx):
        try:
            follow_article = register[idx + 1]
        except IndexError:
            return article_text
        re_match = re.search(r"SPALTE_START=(\d{1,4})", article_text)
        if not re_match:
            return article_text
        start_column = int(re_match.group(1))
        start_follow_article = follow_article.chapter_objects[0].start
        if start_follow_article != start_column + 1:
            return article_text
        return article_text.replace("SPALTE_END=OFF", f"SPALTE_END={start_follow_article}")


if __name__ == "__main__":  # pragma: no cover
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    with ReImporter(wiki=WS_WIKI, debug=True, log_to_wiki=False) as bot:
        bot.run()
