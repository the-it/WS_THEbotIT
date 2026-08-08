import re
from datetime import datetime

from pywikibot import Category, Page, Site
from pywikibot.site import BaseSite

from service.ws_re.register.lemma import Lemma
from service.ws_re.register.register_types.volume import VolumeRegister
from service.ws_re.register.registers import Registers
from service.ws_re.scanner.tasks.adjust_author import adjust_author, get_author_mapping
from service.ws_re.template import RE_DATEN, ReDatenException
from service.ws_re.template.article import Article
from service.ws_re.template.re_page import RePage
from service.ws_re.volumes import Volumes
from tools import save_if_changed
from tools.bots.cloud_bot import CloudBot

CATEGORY_LINE_REGEX = re.compile(r"^\[\[Kategorie:[^\]]+\]\][^\n]*$")


def _split_categories(text: str) -> tuple[str, str]:
    """
    Split a text block at the end of a page into the text itself and the categories that follow it.

    :return: text without the categories, the categories
    """
    lines = text.split("\n")
    categories: list[str] = []
    while lines and (not lines[-1].strip() or CATEGORY_LINE_REGEX.match(lines[-1].strip())):
        line = lines.pop().strip()
        if line:
            categories.insert(0, line)
    return "\n".join(lines).strip(), "\n".join(categories)


class ReImporter(CloudBot):
    _STORE_CATEGORY = "RE:Stammdaten überprüfen"
    _SHORT_TEXT_CATEGORY = "RE:Kurztext überprüfen"
    _PER_NIGHT = 5
    _MAX_CAT = 1000

    def __init__(
        self,
        wiki: BaseSite | None = None,
        debug: bool = True,
        log_to_screen: bool = True,
        log_to_wiki: bool = True,
        send_metrics: bool = False,
    ):
        super().__init__(wiki, debug, log_to_screen, log_to_wiki, send_metrics)
        self.registers = Registers(update_data=True)
        self.new_articles: dict[str, dict[str, str]] = {}
        self.author_mapping = get_author_mapping()
        self._create_neuland()
        self.current_year = datetime.now().year
        self.max_create = min(
            self._PER_NIGHT, self._MAX_CAT - len(list(Category(self.wiki, self._STORE_CATEGORY).articles()))
        )

    def _create_neuland(self):
        for number in [1, 2, 3, 4, 5, 6, 7, 11, 12, 13]:
            neuland = Page(self.wiki, f"Wikisource:RE-Werkstatt/Neuland {number}")
            for raw in re.finditer(
                r"(\{\{REDaten.*?\{\{REAutor\|.*?\}\})\n\d{1,5}\s*„RE:(.*?)“", neuland.text, re.DOTALL
            ):
                lemma = raw.group(2)
                article = raw.group(1)
                if match := re.search(r"BAND=(.{1,10})\n", article):
                    band = match.group(1)
                    if band not in self.new_articles:
                        self.new_articles[band] = {}
                    self.new_articles[band][lemma] = article

    def task(self):
        edit_count = 0
        for register in self.registers.volumes.values():
            if edit_count >= self.max_create:
                break
            for idx, article in enumerate(register):
                if article.proof_read is None:
                    lemma = Page(self.wiki, f"RE:{article.lemma}")
                    article_text = self._compose_article_text(register, idx, article)
                    if lemma.exists():
                        # the lemma is already there, the article of this issue is missing on it
                        if self._add_article(lemma, register.volume.name, article_text):
                            edit_count += 1
                    else:
                        self._create_lemma(lemma, article_text)
                        edit_count += 1
                if edit_count >= self.max_create:
                    self.logger.info(
                        f"Edited {edit_count} articles. Last article was [[RE:{article.lemma}]]"
                        f" in {register.volume.name}"
                    )
                    break
        return True

    def _compose_article_text(self, register: VolumeRegister, idx: int, article: Lemma) -> str:
        article_text = self.get_text(article.volume.name, article.lemma)
        if not article_text:
            pre_article = register[idx - 1] if idx > 0 else None
            try:
                post_article = register[idx + 1]
            except IndexError:
                post_article = None
            article_text = self.get_text_backup(article.volume.name, article, pre_article, post_article)
        article_text = adjust_author(article_text, self.author_mapping)
        article_text = self.adjust_end_column(article_text, register, idx)
        return article_text.replace("KORREKTURSTAND=Platzhalter", "KORREKTURSTAND=unvollständig")

    def _create_lemma(self, lemma: Page, article_text: str):
        article_text = (
            f"{article_text}\n[[Kategorie:{self._STORE_CATEGORY}]]\n[[Kategorie:{self._SHORT_TEXT_CATEGORY}]]"
        )
        save_if_changed(lemma, article_text, "Automatisch generiert")

    def _add_article(self, lemma: Page, band: str, article_text: str) -> bool:
        """
        Add the article of one issue to an already existing lemma. The article is placed in the order of the
        issues, all NACHTRAG/ÜBERSCHRIFT flags of the page are adjusted afterwards.

        :param lemma: page of the existing lemma
        :param band: issue the new article belongs to
        :param article_text: complete text of the new article
        :return: True if the page was altered
        """
        if "SPALTE_START=OFF" in article_text:
            # without a start column the register data is too poor to add something to an existing lemma
            self.logger.info(f"No start column for the article of {band} in [[{lemma.title()}]].")
            return False
        if lemma.isRedirectPage():
            # a redirect isn't a RE article, the redirect must be resolved by hand first
            self.logger.info(f"[[{lemma.title()}]] is a redirect, the article of {band} can't be added.")
            return False
        try:
            re_page = RePage(lemma)
        except ReDatenException as error:
            self.logger.error(f"Can't parse [[{lemma.title()}]] to add the article of {band}. {error.args[0]}")
            return False
        self.split_trailing_categories(re_page)
        try:
            position = self.get_insert_position(re_page, band)
        except ReDatenException as error:
            self.logger.error(f"Can't sort the article of {band} into [[{lemma.title()}]]. {error.args[0]}")
            return False
        if position is None:
            # the article of this issue is already present, nothing to do
            return False
        try:
            new_article = Article.from_text(article_text)
        except ReDatenException as error:
            self.logger.error(f"Can't create an article of {band} for [[{lemma.title()}]]. {error.args[0]}")
            return False
        if short_text := self.get_short_text(re_page):
            # the lemma has a checked short text already, use it instead of the one from the register
            new_article["KURZTEXT"].value = short_text
        else:
            re_page.add_error_category(self._SHORT_TEXT_CATEGORY)
        re_page.insert(position, new_article)
        self.adjust_nachtrag(re_page)
        re_page.add_error_category(self._STORE_CATEGORY)
        try:
            re_page.save(f"Automatisch ergänzter Artikel aus Band {band}")
        except ReDatenException as error:
            self.logger.error(f"Can't save [[{lemma.title()}]] with the added article of {band}. {error.args[0]}")
            return False
        return True

    @staticmethod
    def get_insert_position(re_page: RePage, band: str) -> int | None:
        """
        Determine where the article of an issue belongs on a page. The articles are sorted by issue, an article
        of a later issue is placed behind the articles of all earlier issues.

        :param re_page: page the article should be added to
        :param band: issue of the new article
        :return: index in the article list of the page, None if the page already has an article of this issue
        """
        volumes = Volumes()
        sort_key = volumes[band].sort_key
        position: int | None = None
        for idx, item in enumerate(re_page):
            if not isinstance(item, Article) or item.article_type != RE_DATEN:
                continue
            existing_band = str(item["BAND"].value)
            if existing_band == band:
                return None
            if position is None and volumes[existing_band].sort_key > sort_key:
                position = idx
        if position is not None:
            return position
        # the new article is the last one, but the categories at the end of the page must stay at the end
        last_item = re_page[-1]
        if isinstance(last_item, str):
            text, categories = _split_categories(last_item)
            if categories and not text:
                return len(re_page) - 1
        return len(re_page)

    @staticmethod
    def get_short_text(re_page: RePage) -> str:
        """the short text that is already present on the page, empty if no article of the page has one"""
        for article in re_page.only_articles:
            if article.article_type == RE_DATEN and (short_text := str(article["KURZTEXT"].value)):
                return short_text
        return ""

    @staticmethod
    def split_trailing_categories(re_page: RePage):
        """
        Split the categories at the end of a page from the text that belongs to the last article of the page.
        Only then a new article can be placed between that text and the categories.
        """
        last_item = re_page[-1]
        if not isinstance(last_item, str):
            return
        text, categories = _split_categories(last_item)
        if not categories or not text:
            return
        re_page[len(re_page) - 1] = text
        re_page.insert(len(re_page), categories)

    @staticmethod
    def adjust_nachtrag(re_page: RePage):
        """
        The first article of a page is the main article, everything after it is a Nachtrag, only the first
        Nachtrag bears the heading (same rules as the NAUETask).
        """
        daten_articles = [item for item in re_page if isinstance(item, Article) and item.article_type == RE_DATEN]
        for idx, item in enumerate(daten_articles):
            item["NACHTRAG"].value = idx > 0
            item["ÜBERSCHRIFT"].value = idx == 1

    def get_text(self, band: str, article: str) -> str | None:
        band_dict = self.new_articles.get(band, None)
        if band_dict:
            article_text = band_dict.get(article, None)
            if article_text:
                return article_text
        return None

    @staticmethod
    def get_text_backup(
        band: str, article: Lemma, pre_article: Lemma | None = None, post_article: Lemma | None = None
    ) -> str:
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
        spalte_end: str | int = "OFF"
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
