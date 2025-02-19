import re
from datetime import timedelta, datetime
from typing import Tuple

from pywikibot import Site, Page

from service.list_bots._base import is_empty_value, has_value
from service.list_bots.author_info import AuthorInfo
from service.list_bots.list_bot import ListBot
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
        self.new_data_model = datetime(2025, 2, 15, 23)
        self.timeout = timedelta(seconds=240)

    def get_lemma_list(self) -> Tuple[list[str], int]:
        searcher = PetScan()
        searcher.add_namespace(0)  # search in main namespace
        searcher.add_positive_category("Gedicht")
        searcher.set_search_depth(3)
        self.logger.info(f"Searching for lemmas with {searcher}")
        return searcher.get_combined_lemma_list(self.get_check_dict(), timeframe=72)

    def sort_to_list(self) -> list[dict[str, str]]:
        poem_list = list(self.data.values())
        return sorted(poem_list, key=lambda poem_dict: (poem_dict["sortkey"], poem_dict["lemma"]))

    def enrich_dict(self, page: Page, item_dict: dict[str, str]) -> None:
        if has_value("author", item_dict):
            try:
                item_dict["author"] = self._clean_author(item_dict["author"])
                author_page = Page(self.wiki, item_dict["author"])
                if author_page.isRedirectPage():
                    author_page = author_page.getRedirectTarget()
                    item_dict["author"] = author_page.title()
                author_dict = AuthorInfo(author_page).get_author_dict()
                item_dict["first_name"] = author_dict["first_name"]
                item_dict["last_name"] = author_dict["last_name"]
                item_dict["sortkey_auth"] = author_dict["sortkey"]
            except ValueError:
                self.logger.error(f"Can't process author {item_dict['author']}")
        if is_empty_value("sortkey", item_dict):
            if has_value("title", item_dict):
                item_dict["sortkey"] = item_dict["title"]
            else:
                item_dict["sortkey"] = item_dict["lemma"]
        item_dict["first_line"] = self.get_first_line(page.text)
        for item in ["title", "author", "first_name", "last_name",
                     "sortkey_auth", "creation", "publish", "sortkey", "first_line"]:
            if item not in item_dict:
                item_dict[item] = ""

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
            string_list.append(f"|[[{self.get_print_title(poem_dict)}]]")
            string_list.append(f"|{poem_dict['first_line']}")
            string_list.append(f"|{self.get_print_year(poem_dict)}")
        string_list.append("|}")
        string_list.append('')
        string_list.append("== Fußnoten ==")
        string_list.append("<references/>")
        string_list.append('')
        string_list.append("{{SORTIERUNG:Gedichte #Liste der}}")
        string_list.append("[[Kategorie:Listen]]")
        return "\n".join(string_list)

    @staticmethod
    def get_print_title(poem_dict: dict[str, str]) -> str:
        if has_value("title", poem_dict):
            if poem_dict["title"] != poem_dict["lemma"]:
                return f"{poem_dict['lemma']}|{poem_dict['title']}"
            return poem_dict['lemma']
        return f"{poem_dict['lemma']}|{poem_dict['lemma']} NO TITLE"

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
        if has_value("author", poem_dict) and show_author != poem_dict["author"]:
            return f"[[{poem_dict['author']}|{show_author}]]"
        return f"[[{poem_dict['author']}]]"

    @staticmethod
    def get_print_year(poem_dict: dict[str, str]) -> str:
        if has_value("creation", poem_dict):
            return poem_dict["creation"]
        if has_value("publish", poem_dict):
            return f"{poem_dict['publish']} (veröff.)"
        return ""

    POEM_REGEX = re.compile(r"<poem>(.*?)<\/poem>", re.DOTALL)
    ZEILE_REGEX = re.compile(r"\{\{Zeile\|5\}\}")
    HEADLINE_REGEX = re.compile(r"'''.+?'''")
    FIRST_LINE_REGEX = re.compile(r"<!-- ?first_line ?-->")

    def get_first_line(self, text):
        text = TemplateExpansion(text, self.wiki).expand()
        if self.FIRST_LINE_REGEX.search(text):
            for line in self._split_lines(text):
                if self.FIRST_LINE_REGEX.search(line):
                    return line
        if match := self.POEM_REGEX.search(text):
            lines: str = match.group(1)
            lines_list = self._split_lines(lines)
            if self.ZEILE_REGEX.search(lines):
                for idx, line in enumerate(lines_list):
                    if self.ZEILE_REGEX.search(line):
                        return lines_list[idx - 4]
            elif self.HEADLINE_REGEX.search(lines):
                found = False
                for idx, line in enumerate(lines_list):
                    if self.HEADLINE_REGEX.search(line):
                        found = True
                        continue
                    if found:
                        return line
        return ""

    @staticmethod
    def _split_lines(lines: str) -> list[str]:
        lines_list = []
        for line in lines.splitlines():
            if line.strip():
                lines_list.append(line)
        return lines_list

    LINK_REGEX = re.compile(r"\[\[([^\]]*?)\]\]")

    def _clean_author(self, author: str) -> str:
        if match := self.LINK_REGEX.search(author):
            return match.group(1)
        return author


if __name__ == "__main__":
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    with PoemList(wiki=WS_WIKI, debug=True) as bot:
        bot.run()
