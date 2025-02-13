from copy import deepcopy
from datetime import timedelta, datetime
from typing import Tuple

from pywikibot import Page, Site


from service.list_bots.author_info import AuthorDict, AuthorInfo
from tools.bots import BotException
from tools.bots.cloud.cloud_bot import CloudBot
from tools.date_conversion import DateConversion
from tools.petscan import PetScan





class AuthorList(CloudBot):
    def __init__(self, wiki: Site = None, debug: bool = True, log_to_screen: bool = True, log_to_wiki: bool = True):
        super().__init__(wiki, debug, log_to_screen, log_to_wiki)
        self.new_data_model = datetime(2025, 2, 13, 9)
        self.timeout = timedelta(minutes=3)

    def __enter__(self):
        super().__enter__()
        if not self.data:
            self.logger.warning("Try to get the deprecated data back.")
            try:
                self.data.get_deprecated()
            except BotException:
                self.logger.warning("There isn't deprecated data to reload.")
        if self.data_outdated():
            self.data.assign_dict({})
        return self

    def task(self) -> bool:
        self.logger.info("Processing lemmas.")
        self.process_lemmas()
        self.logger.info("Sorting author list.")
        author_list = self.sort_to_list()
        self.logger.info("Printing text.")
        new_text = self.print_author_list(author_list)
        author_list_page = Page(self.wiki, "Liste der Autoren")
        old_text = author_list_page.text
        if new_text[150:] not in old_text:  # compare all but the date
            author_list_page.text = new_text
            author_list_page.save("Die Liste wurde auf den aktuellen Stand gebracht.", bot=True)
        else:
            self.logger.info("Heute gab es keine Änderungen, daher wird die Seite nicht überschrieben.")
        return True

    def process_lemmas(self):
        lemma_list, unprocessed_lemmas = self.get_lemma_list()
        for idx, lemma in enumerate(lemma_list):
            clean_lemma = lemma.strip(":").replace("_", " ")
            self.logger.debug(f"{idx + 1}/{unprocessed_lemmas} {clean_lemma}")
            page = Page(self.wiki, lemma)
            author_dict = AuthorInfo(page).get_author_dict()
            author_dict["title"] = clean_lemma
            author_dict["check"] = datetime.now().strftime("%Y%m%d%H%M%S")
            self.data[lemma] = author_dict
            if (idx - 10 > unprocessed_lemmas) and self._watchdog():
                break

    def get_check_dict(self):
        return {author: self.data[author]["check"] for author in self.data}

    def get_lemma_list(self) -> Tuple[list[str], int]:
        searcher = PetScan()
        searcher.add_namespace(0)  # search in main namespace
        searcher.add_positive_category("Autoren")
        searcher.add_yes_template("Personendaten")
        self.logger.info(f"Searching for lemmas with {searcher}")
        return searcher.get_combined_lemma_list(self.get_check_dict(), timeframe=72)



    def sort_to_list(self) -> list[AuthorDict]:
        author_list = []
        for author in self.data.values():
            author = deepcopy(author)
            author["birth_sort"] = str(DateConversion(author["birth"]))
            author["death_sort"] = str(DateConversion(author["death"]))
            author_list.append(author)
        return sorted(author_list, key=lambda author_dict: (author_dict["sortkey"], author_dict["birth_sort"]))

    def print_author_list(self, author_list: list[AuthorDict]) -> str:
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
        for author_dict in author_list:
            string_list.append("|-")
            if 'last_name' in author_dict and 'first_name' in author_dict:
                string_list.append(f"|data-sort-value=\"{author_dict['sortkey']}\"|"
                                   f"[[{author_dict['title']}|{author_dict['last_name']}, "
                                   f"{author_dict['first_name']}]]")
            elif 'first_name' in author_dict:
                string_list.append(f"|data-sort-value=\"{author_dict['sortkey']}\"|"
                                   f"[[{author_dict['title']}|{author_dict['first_name']}]]")
            else:
                string_list.append(f"|data-sort-value=\"{author_dict['sortkey']}\"|"
                                   f"[[{author_dict['title']}|{author_dict['last_name']}]]")
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


if __name__ == "__main__":
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    with AuthorList(wiki=WS_WIKI, debug=True) as bot:
        bot.run()
