from copy import deepcopy
from datetime import timedelta, datetime
from typing import Tuple

from pywikibot import Page, Site

from service.list_bots._base import has_value
from service.list_bots.author_info import AuthorInfo
from service.list_bots.list_bot import ListBot
from tools.date_conversion import DateConversion
from tools.petscan import PetScan


class AuthorList(ListBot):
    LIST_LEMMA = "Liste der Autoren"

    def __init__(self, wiki: Site = None, debug: bool = True, log_to_screen: bool = True, log_to_wiki: bool = True):
        super().__init__(wiki, debug, log_to_screen, log_to_wiki)
        self.new_data_model = datetime(2025, 2, 17, 23)
        self.timeout = timedelta(minutes=2)

    def get_page_infos(self, page: Page) -> dict:
        return AuthorInfo(page).get_author_dict()

    def get_check_dict(self):
        return {author: self.data[author]["check"] for author in self.data}

    def get_lemma_list(self) -> Tuple[list[str], int]:
        searcher = PetScan()
        searcher.add_namespace(0)  # search in main namespace
        searcher.add_positive_category("Autoren")
        searcher.add_yes_template("Personendaten")
        self.logger.info(f"Searching for lemmas with {searcher}")
        return searcher.get_combined_lemma_list(self.get_check_dict(), timeframe=72)

    def sort_to_list(self) -> list[dict[str, str]]:
        author_list = []
        for author in self.data.values():
            author = deepcopy(author)
            author["birth_sort"] = str(DateConversion(author["birth"]))
            author["death_sort"] = str(DateConversion(author["death"]))
            author_list.append(author)
        return sorted(author_list, key=lambda author_dict: (author_dict["sortkey"], author_dict["birth_sort"]))

    def print_list(self, item_list: list[dict[str, str]]) -> str:
        start_of_run = self.status.current_run.start_time
        string_list = []
        string_list.append(f"Diese Liste der Autoren enthält alle {len(self.data)}<ref>Stand: "
                           f"{start_of_run.day}.{start_of_run.month}.{start_of_run.year}, "
                           f"{start_of_run.strftime('%H:%M')} (UTC)</ref> Autoren, "
                           f"zu denen in Wikisource eine Autorenseite existiert.")
        string_list.append("Die Liste kann mit den Buttons neben den Spaltenüberschriften"
                           " nach der jeweiligen Spalte sortiert werden.")
        string_list.append("<!--")
        string_list.append("Diese Liste wurde durch ein Computerprogramm erstellt, "
                           "das die Daten verwendet, "
                           "die aus den Infoboxen auf den Autorenseiten stammen.")
        string_list.append("Sollten daher Fehler vorhanden sein, "
                           "sollten diese jeweils dort korrigiert werden.")
        string_list.append("-->")
        string_list.append("{{Tabellenstile}}")
        string_list.append("{|class=\"wikitable sortable tabelle-kopf-fixiert\"")
        string_list.append("!style=\"width:20%\"| Name")
        string_list.append("!data-sort-type=\"text\" style=\"width:15%\"| Geb.-datum")
        string_list.append("!data-sort-type=\"text\" style=\"width:15%\"| Tod.-datum")
        string_list.append("!class=\"unsortable\" style=\"width:50%\"| Beschreibung")
        for author_dict in item_list:
            string_list.append("|-")
            string_list.append(f"|data-sort-value=\"{author_dict['sortkey']}\"|"
                               f"[[{author_dict['lemma']}|{self.get_author_line(author_dict)}]]")
            string_list.append(f"|data-sort-value=\"{author_dict['birth_sort']}\"|{author_dict['birth']}")
            string_list.append(f"|data-sort-value=\"{author_dict['death_sort']}\"|{author_dict['death']}")
            string_list.append(f"|{author_dict['description']}")
        string_list.append("|}")
        string_list.append('')
        string_list.append("== Anmerkungen ==")
        string_list.append("<references/>")
        string_list.append('')
        string_list.append("{{SORTIERUNG:Autoren #Liste der}}")
        string_list.append("[[Kategorie:Listen]]")
        string_list.append("[[Kategorie:Autoren|!]]")
        return "\n".join(string_list)

    @staticmethod
    def get_author_line(author_dict: dict[str, str]) -> str:
        if has_value("last_name", author_dict) and has_value("first_name", author_dict):
            return f"{author_dict['last_name']}, {author_dict['first_name']}"
        if has_value("first_name", author_dict):
            return author_dict['first_name']
        return author_dict['last_name']


if __name__ == "__main__":
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    with AuthorList(wiki=WS_WIKI, debug=True) as bot:
        bot.run()
