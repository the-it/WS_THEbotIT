import re
from contextlib import suppress
from datetime import timedelta, datetime
from functools import lru_cache
from typing import Tuple

from pywikibot import Site, Page
from pywikibot.exceptions import InvalidTitleError

from service.list_bots._base import is_empty_value, has_value, get_page_infos
from service.list_bots.author_info import AuthorInfo
from service.list_bots.list_bot import ListBot
from tools.date_conversion import DateConversion
from tools.petscan import PetScan
from tools.template_expansion import TemplateExpansion


class PoemList(ListBot):
    PROPERTY_TEMPLATE = "Textdaten"
    PROPERTY_MAPPING = {
        "title": "TITEL",
        "author": "AUTOR",
        "creation": "ENTSTEHUNGSJAHR",
        "publish": "ERSCHEINUNGSJAHR",
    }
    LIST_LEMMA = "Liste der Gedichte/New"

    def __init__(self, wiki: Site = None, debug: bool = True, log_to_screen: bool = True, log_to_wiki: bool = True):
        super().__init__(wiki, debug, log_to_screen, log_to_wiki)
        self.new_data_model = datetime(2025, 2, 27, 23)
        self.timeout = timedelta(minutes=2)

    def get_lemma_list(self) -> Tuple[list[str], int]:
        searcher = PetScan()
        searcher.add_namespace(0)  # search in main namespace
        searcher.add_positive_category("Gedicht")
        searcher.add_negative_category("Unkorrigiert")
        searcher.add_negative_category("Unvollständig")
        searcher.set_search_depth(3)
        self.logger.info(f"Searching for lemmas with {searcher}")
        return searcher.get_combined_lemma_list(self.get_check_dict(), timeframe=72)

    def sort_to_list(self) -> list[dict[str, str]]:
        poem_list = list(self.data.values())
        return sorted(poem_list, key=lambda poem_dict: (poem_dict["sortkey"], poem_dict["lemma"]))

    def get_page_infos(self, page: Page) -> dict[str, str]:
        if "{{GartenlaubenArtikel" in page.text:
            return get_page_infos(
                page.text,
                "GartenlaubenArtikel",
                {
                    "title": "TITEL",
                    "author": "AUTOR",
                    "publish": "JAHR",
                }
            )
        if "{{Kapitel" in page.text:
            return_dict = self.get_kapitel_page_infos(page)
            return return_dict

        # default processing of the Textdaten template
        return get_page_infos(page.text, self.PROPERTY_TEMPLATE, self.PROPERTY_MAPPING)

    def get_kapitel_page_infos(self, page) -> dict[str, str]:
        kapitel_dict = get_page_infos(
            page.text,
            "Kapitel",
            {
                "part": "TITELTEIL",
            }
        )
        part = 2
        if has_value("part", kapitel_dict):
            part = int(kapitel_dict["part"])
        title_parts = page.title().split("/")
        try:
            page_dict = {"title": title_parts[part - 1]}
        except IndexError as err:
            raise ValueError(f"Referenced part of the title doesn't exists for {page.title()}") from err
        parent_page = Page(self.wiki, title_parts[0])
        if not parent_page.exists():
            raise ValueError(f"Page {title_parts[0]} as parent page for {page.title()} does not exist")
        return_dict = get_page_infos(parent_page.text, self.PROPERTY_TEMPLATE, self.PROPERTY_MAPPING)
        return_dict["title"] = page_dict["title"]
        return return_dict

    def enrich_dict(self, page: Page, item_dict: dict[str, str]) -> None:
        if has_value("author", item_dict):
            try:
                item_dict["author"] = self._clean_author(item_dict["author"])
                author_page = Page(self.wiki, item_dict["author"])
                if author_page.isRedirectPage():
                    author_page = author_page.getRedirectTarget()
                    item_dict["author"] = author_page.title()
                author_dict = self.get_author_dict(author_page)
                item_dict["first_name"] = author_dict["first_name"]
                item_dict["last_name"] = author_dict["last_name"]
                item_dict["sortkey_auth"] = author_dict["sortkey"]
            except (ValueError, InvalidTitleError):
                self.logger.error(f"Can't process author {item_dict['author']} of lemma {item_dict['lemma']}")
                item_dict["no_lemma_auth"] = "yes"
        if has_value("title", item_dict):
            item_dict["title"] = self.clean_lemma_link(item_dict["title"])
        item_dict["sortkey"] = self.get_sortkey(item_dict, page.text)
        item_dict["first_line"] = self.get_first_line(page.text)
        item_dict["year"] = self.get_year(item_dict)
        with suppress(KeyError):
            item_dict.pop("creation")
        with suppress(KeyError):
            item_dict.pop("publish")
        for item in ["title", "author", "first_name", "last_name",
                     "sortkey_auth", "year", "sortkey", "first_line"]:
            if item not in item_dict:
                item_dict[item] = ""

    @staticmethod
    @lru_cache(maxsize=1000)
    def get_author_dict(author_page):
        author_dict = AuthorInfo(author_page).get_author_dict()
        return author_dict

    SORTIERUNG_REGEX = re.compile(r"\{\{(?:SORTIERUNG|DEFAULTSORT):(.*?)\}\}")
    ARTIKEL_REGEX = re.compile(r"(Das|Die|Der) (.*)$")

    def get_sortkey(self, item_dict: dict[str, str], text: str) -> str:
        if match := self.SORTIERUNG_REGEX.search(text):
            return match.group(1).strip()
        alternative_sortkey = item_dict["lemma"]
        if has_value("title", item_dict):
            alternative_sortkey = item_dict["title"]
        if match := self.ARTIKEL_REGEX.search(alternative_sortkey):
            return f"{match.group(2)} #{match.group(1)}"
        return alternative_sortkey

    def print_list(self, item_list: list[dict[str, str]]) -> str:
        start_of_run = self.status.current_run.start_time
        string_list = []
        string_list.append(f"Diese Liste der Gedichte enthält alle {len(self.data)}<ref>Stand: "
                           f"{start_of_run.day}.{start_of_run.month}.{start_of_run.year}, "
                           f"{start_of_run.strftime('%H:%M')} (UTC)</ref> Gedichte, "
                           f"die in Wikisource digitalisiert wurden.")
        string_list.append("Die Liste kann mit den Buttons neben den Spaltenüberschriften"
                           " nach der jeweiligen Spalte sortiert werden.")
        string_list.append("<!--")
        string_list.append("Diese Liste wurde durch ein Computerprogramm erstellt, "
                           "das die Daten verwendet, "
                           "die aus den Infoboxen auf den Gedichtseiten stammen.")
        string_list.append("Sollten daher Fehler vorhanden sein, "
                           "sollten diese jeweils dort korrigiert werden.")
        string_list.append("-->")
        string_list.append("{|class=\"prettytable sortable tabelle-kopf-fixiert\" {{prettytable}}")
        string_list.append("! Autor")
        string_list.append("! Titel")
        string_list.append("! Gedichtanfang")
        string_list.append("! Jahr")
        for poem_dict in item_list:
            string_list.append("|-")
            string_list.append(f"|{self.get_print_author(poem_dict)}")
            string_list.append(f"|{self.get_print_title(poem_dict)}")
            string_list.append(f"|{poem_dict['first_line']}")
            string_list.append(f"|{poem_dict['year']}")
        string_list.append("|}")
        string_list.append('')
        string_list.append("== Fußnoten ==")
        string_list.append("<references/>")
        string_list.append("<references group=\"WS\"/>")
        string_list.append('')
        string_list.append("{{SORTIERUNG:Gedichte #Liste der}}")
        string_list.append("[[Kategorie:Listen]]")
        return "\n".join(string_list)

    @staticmethod
    def get_print_title(poem_dict: dict[str, str]) -> str:
        title = poem_dict["lemma"]
        link = f"{title}"
        if has_value("title", poem_dict) and poem_dict["title"] != poem_dict["lemma"]:
            title = poem_dict['title']
            link = f"{poem_dict['lemma']}|{title}"
        sortkey = ""
        if has_value("sortkey", poem_dict) and poem_dict['sortkey'] != title:
            sortkey = f"data-sort-value=\"{poem_dict['sortkey']}\"|"

        return f"{sortkey}[[{link}]]"

    @staticmethod
    def get_print_author(poem_dict: dict[str, str]) -> str:
        if is_empty_value("last_name", poem_dict) and is_empty_value("first_name", poem_dict):
            show_author = poem_dict["author"]
        elif is_empty_value("last_name", poem_dict):
            show_author = poem_dict["first_name"]
        elif is_empty_value("first_name", poem_dict):
            show_author = poem_dict["last_name"]
        else:
            show_author = f"{poem_dict['last_name']}, {poem_dict['first_name']}"
        if has_value("sortkey_auth", poem_dict) and poem_dict["sortkey_auth"] != show_author:
            return f"data-sort-value=\"{poem_dict['sortkey_auth']}\"|[[{poem_dict['author']}|{show_author}]]"
        if not show_author and not poem_dict["author"]:
            return ""
        if has_value("no_lemma_auth", poem_dict):
            return poem_dict["author"]
        if has_value("author", poem_dict) and show_author != poem_dict["author"]:
            return f"[[{poem_dict['author']}|{show_author}]]"
        return f"[[{poem_dict['author']}]]"

    POEM_REGEX = re.compile(r"<poem>(.*?)<\/poem>", re.DOTALL)
    ZEILE_REGEX = re.compile(r"\{\{[Zz]eile\|5\}\}")
    HEADLINE_REGEX = re.compile(r"'''?.+?'''?")
    FIRST_LINE_REGEX = re.compile(r"<!-- ?(?:first_line|[eE]rste ?[zZ]eile) ?-->")

    def get_first_line(self, text):
        text = TemplateExpansion(text, self.wiki).expand()
        lines_list = self._split_lines(text)
        # if a first line is annotated, this take precedent
        if self.FIRST_LINE_REGEX.search(text):
            for line in lines_list:
                if self.FIRST_LINE_REGEX.search(line):
                    return self._clean_first_line(line)
        # identifying the first line by searching for the Zeile annotation of the 5th line is the most reliable method
        if self.ZEILE_REGEX.search(text):
            for idx, line in enumerate(lines_list):
                if self.ZEILE_REGEX.search(line):
                    return self._clean_first_line(lines_list[idx - 4])
        # don't do this for this nights run ... let's see how many empty lines we will get
        if match := self.POEM_REGEX.search(text):
            lines: str = match.group(1)
            lines_list = self._split_lines(lines)
            if not self.HEADLINE_REGEX.search(lines_list[0]):
                if lines_list[1].strip():
                    return self._clean_first_line(lines_list[0])
        return ""

    CLEAN_POEM_REGEX = re.compile(r"<\/?poem>")
    CLEAN_SEITE_REGEX = re.compile(r"\{\{Seite(?:PR1)?\|[^\}]*?\}\}")
    CLEAN_IDT = re.compile(r"^\{\{[Ii][Dd][Tt]2?[^\}]*?\}\}")
    CLEAN_INFO_BOX = re.compile(r"\|[A-Z]+ ?= ?[a-z]+")

    def _clean_first_line(self, line: str) -> str:
        for regex in [self.CLEAN_POEM_REGEX, self.CLEAN_SEITE_REGEX, self.CLEAN_IDT, self.CLEAN_INFO_BOX]:
            line = regex.sub("", line)
        if line == "}}":
            return ""
        return line.strip(" :")

    def _split_lines(self, lines: str) -> list[str]:
        lines_list = []
        for line in lines.splitlines():
            line = self.CLEAN_POEM_REGEX.sub("", line)
            if line.strip():
                lines_list.append(line)
        return lines_list

    LINK_REGEX = re.compile(r"\[\[([^\]]*?)\]\]")

    def _clean_author(self, author: str) -> str:
        if match := self.LINK_REGEX.search(author):
            return match.group(1)
        return author

    YEAR_REGEX = re.compile(r"^\d{4}$")

    def get_year(self, item_dict: dict[str, str]) -> str:
        year = ""
        if has_value("creation", item_dict):
            year = item_dict["creation"]
        elif has_value("publish", item_dict):
            year = item_dict['publish']
        year = year.strip("[]")
        if year and not self.YEAR_REGEX.search(year):
            with suppress(ValueError):
                year = f"data-sort-value=\"{DateConversion(year)}\"|{year}"
        return year

    def post_infos(self):
        has_first_line = 0
        for poem in self.data.values():
            if poem["first_line"]:
                has_first_line += 1
        self.logger.info(f"{(has_first_line / len(self.data)) * 100:.2f}% of poems have a first line.")

    TITLE_LINK_REGEX = re.compile(r"\[\[(?:[^\]\|]*?\|)?(.*?)\]\]")

    def clean_lemma_link(self, potential_link: str) -> str:
        return self.TITLE_LINK_REGEX.sub(r"\1", potential_link)


if __name__ == "__main__":
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    with PoemList(wiki=WS_WIKI, debug=True) as bot:
        bot.run()
