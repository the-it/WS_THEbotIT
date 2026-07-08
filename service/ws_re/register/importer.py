import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from pywikibot import Site, Page, Category

from service.ws_re.register.lemma import Lemma
from service.ws_re.register.registers import Registers
from service.ws_re.scanner.tasks.adjust_author import adjust_author, get_author_mapping
from tools import save_if_changed
from tools.bots.cloud_bot import CloudBot


class ReImporter(CloudBot):
    _STORE_CATEGORY = "RE:Stammdaten überprüfen"
    _PER_NIGHT = 100
    _MAX_CAT = 1000

    def __init__(self, wiki: Site = None, debug: bool = True,
                 log_to_screen: bool = True, log_to_wiki: bool = True):
        super().__init__(wiki, debug, log_to_screen, log_to_wiki)
        self.registers = Registers(update_data=True)
        self.new_articles: dict[str, dict[str, str]] = {}
        self.author_mapping = get_author_mapping()
        self.tm_set = self.load_tm_set()
        self._create_neuland()
        self.current_year = datetime.now().year
        self.max_create = min(self._PER_NIGHT,
                              self._MAX_CAT - len(list(Category(self.wiki, self._STORE_CATEGORY).articles())))

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
                    lemma = Page(self.wiki, f"RE:{article.lemma}")
                    if not lemma.exists():
                        article_text = self.get_text(article.volume.name, article.lemma)
                        if not article_text:
                            pre_article = register[idx - 1] if idx > 0 else None
                            try:
                                post_article = register[idx + 1]
                            except IndexError:
                                post_article = None
                            article_text = self.get_text_backup(article.volume.name, article,
                                                                pre_article, post_article)
                        article_text = adjust_author(article_text, self.author_mapping)
                        article_text = self.adjust_end_column(article_text, register, idx)
                        article_text = article_text.replace("KORREKTURSTAND=Platzhalter",
                                                            "KORREKTURSTAND=unvollständig")
                        category = self._STORE_CATEGORY
                        if article.lemma in self.tm_set:
                            category += ", Personen"
                        article_text = (f"{article_text}\n[[Kategorie:{category}]]"
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

    @staticmethod
    def get_text_backup(band: str, article: Lemma,
                        pre_article: Optional[Lemma] = None,
                        post_article: Optional[Lemma] = None) -> str:
        if article.previous:
            vorgaenger = article.previous
        elif pre_article is not None:
            vorgaenger = pre_article.lemma
        else:
            vorgaenger = ""
        if article.next:
            nachfolger = article.next
        elif post_article is not None:
            nachfolger = post_article.lemma
        else:
            nachfolger = ""
        spalte_start = article.chapter_objects[0].start if article.chapter_objects else "OFF"
        spalte_end = "OFF"
        if article.chapter_objects and article.chapter_objects[0].end:
            spalte_end = article.chapter_objects[0].end
        author = "OFF"
        if article.chapter_objects and article.chapter_objects[0].author:
            author = article.chapter_objects[0].author
        short_text = article.short_description if article.short_description else ""
        parsed_article = f"""{{{{REDaten
|BAND={band}
|SPALTE_START={spalte_start}
|SPALTE_END={spalte_end}
|VORGÄNGER={vorgaenger}
|NACHFOLGER={nachfolger}
|SORTIERUNG=
|KORREKTURSTAND=unvollständig
|KURZTEXT={short_text}
|WIKIPEDIA=
|WIKISOURCE=
|GND=
|KEINE_SCHÖPFUNGSHÖHE=OFF
|TODESJAHR=
|GEBURTSJAHR=
|NACHTRAG=OFF
|ÜBERSCHRIFT=OFF
|VERWEIS=OFF
}}}}
'''{article.lemma}'''
[...]
{{{{REAutor|{author}}}}}"""
        return parsed_article

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
        if not follow_article.chapter_objects:
            return article_text
        start_follow_article = follow_article.chapter_objects[0].start
        if start_follow_article != start_column + 1:
            return article_text
        return article_text.replace("SPALTE_END=OFF", f"SPALTE_END={start_follow_article}")


if __name__ == "__main__":  # pragma: no cover
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    with ReImporter(wiki=WS_WIKI, debug=True, log_to_wiki=False) as bot:
        bot.run()
