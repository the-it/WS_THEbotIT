from datetime import timedelta, datetime
from typing import TypedDict, Literal, Tuple

from pywikibot import Site

from service.list_bots.list_bot import ListBot
from tools.petscan import PetScan


class PoemDict(TypedDict, total=False):
    title: str
    lemma: str
    author: str
    start_line: str
    creation: str
    publish: str
    proofread: str
    check: str


PoemInfos = Literal["title", "lemma", "author", "start_line", "creation", "publish", "proofread", "check"]


class PoemList(ListBot):
    PROPERTY_TEMPLATE = "Textdaten"
    PROPERTY_MAPPING = {
        "title": "TITEL",
        "author": "AUTOR",
        "creation": "ENTSTEHUNGSJAHR",
        "publish": "ERSCHEINUNGSJAHR",
        "proofread": "BEARBEITUNGSSTAND",
        "sortkey": "SORTIERUNG",
    }
    LIST_LEMMA = "Liste der Gedichte/New"

    def __init__(self, wiki: Site = None, debug: bool = True, log_to_screen: bool = True, log_to_wiki: bool = True):
        super().__init__(wiki, debug, log_to_screen, log_to_wiki)
        self.new_data_model = datetime(2025, 2, 10, 23)
        self.timeout = timedelta(minutes=1)

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

    def print_list(self, poem_list: list[dict[str, str]]) -> str:
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
        string_list.append("{|class=\"prettytable sortable tabelle-kopf-fixiert\"")
        string_list.append("! Nr.")
        string_list.append("! Autor")
        string_list.append("! Titel")
        string_list.append("! Gedichtanfang")
        string_list.append("! Jahr")
        string_list.append("! Stand")
        for idx, poem_dict in enumerate(poem_list):
            string_list.append("|-")
            string_list.append(f"|{idx + 1}")
            if "author" in poem_dict:
                string_list.append(f"|{poem_dict["author"]}")
            else:
                string_list.append("|")
            title = poem_dict["lemma"]
            if "title" in poem_dict:
                if poem_dict["title"] != poem_dict["lemma"]:
                    title = f"{poem_dict['title']}|"
        string_list.append("|}")
        string_list.append('')
        string_list.append("== Fußnoten ==")
        string_list.append("<references/>")
        string_list.append('')
        string_list.append("{{SORTIERUNG:Gedichte #Liste der}}")
        string_list.append("[[Kategorie:Listen]]")
        return "\n".join(string_list)


if __name__ == "__main__":
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    with PoemList(wiki=WS_WIKI, debug=True) as bot:
        bot.run()
