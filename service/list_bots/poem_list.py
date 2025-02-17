from datetime import timedelta, datetime
from typing import Tuple

from pywikibot import Site, Page

from service.list_bots.author_info import AuthorInfo
from service.list_bots.list_bot import ListBot
from tools.petscan import PetScan


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
        self.timeout = timedelta(seconds=60)

    def get_lemma_list(self) -> Tuple[list[str], int]:
        searcher = PetScan()
        searcher.add_namespace(0)  # search in main namespace
        searcher.add_positive_category("Gedicht")
        searcher.set_search_depth(3)
        self.logger.info(f"Searching for lemmas with {searcher}")
        return searcher.get_combined_lemma_list(self.get_check_dict(), timeframe=72)

    def sort_to_list(self) -> list[dict[str, str]]:
        poem_list = [poem for poem in self.data.values()]
        return sorted(poem_list, key=lambda poem_dict: (poem_dict["title"], poem_dict["lemma"]))

    def enrich_dict(self, page: Page, item_dict: dict[str, str]) -> None:
        if item_dict["author"]:
            item_dict["author"] = item_dict["author"].strip("[]")
            author_dict = AuthorInfo(Page(self.wiki, item_dict["author"])).get_author_dict()
            item_dict["first_name"] = author_dict["first_name"]
            item_dict["last_name"] = author_dict["last_name"]
            item_dict["sortkey"] = author_dict["sortkey"]
        for item in ["title", "author", "first_name", "last_name", "sortkey", "creation", "publish"]:
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
        if "title" in poem_dict:
            if poem_dict["title"] != poem_dict["lemma"]:
                return f"{poem_dict['lemma']}|{poem_dict['title']}"
            else:
                return poem_dict['lemma']
        return f"{poem_dict['lemma']}|{poem_dict['lemma']} NO TITLE"

    @staticmethod
    def get_print_author(poem_dict:dict[str, str]) -> str:
        show_author = f"{poem_dict['last_name']}, {poem_dict['first_name']}"
        if not poem_dict["last_name"] and not poem_dict["first_name"]:
            show_author = poem_dict["author"]
        elif not poem_dict["last_name"]:
            show_author = poem_dict["first_name"]
        elif not poem_dict["first_name"]:
            show_author = poem_dict["last_name"]
        if poem_dict["sortkey"] != show_author:
            return f"data-sort-value=\"{poem_dict['sortkey']}\"|[[{poem_dict['author']}|{show_author}]]"
        if show_author != poem_dict["author"]:
            return f"[[{poem_dict['author']}|{show_author}]]"
        return f"[[{poem_dict['author']}]]"


if __name__ == "__main__":
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    with PoemList(wiki=WS_WIKI, debug=True) as bot:
        bot.run()
