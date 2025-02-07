import re
from contextlib import suppress
from copy import deepcopy
from datetime import timedelta, datetime
from math import ceil
from typing import TypedDict, Literal, Tuple, Optional

from pywikibot import ItemPage, Page, Site, Claim
from pywikibot.exceptions import NoPageError

from tools.bots import BotException
from tools.bots.cloud.cloud_bot import CloudBot
from tools.date_conversion import DateConversion
from tools.petscan import PetScan
from tools.template_finder import TemplateFinder, TemplateFinderException
from tools.template_handler import TemplateHandler, TemplateHandlerException

number_to_month = {1: "Januar",
                   2: "Februar",
                   3: "März",
                   4: "April",
                   5: "Mai",
                   6: "Juni",
                   7: "Juli",
                   8: "August",
                   9: "September",
                   10: "Oktober",
                   11: "November",
                   12: "Dezember"}


class AuthorDict(TypedDict, total=False):
    title: str
    first_name: str
    last_name: str
    birth: str
    birth_sort: str
    death: str
    death_sort: str
    description: str
    sortkey: str


AuthorInfos = Literal["title", "first_name", "last_name", "birth", "death", "description", "sortkey"]

_SPACE_REGEX = re.compile(r"\s+")


class AuthorList(CloudBot):
    def __init__(self, wiki: Site = None, debug: bool = True, log_to_screen: bool = True, log_to_wiki: bool = True):
        super().__init__(wiki, debug, log_to_screen, log_to_wiki)
        self.new_data_model = datetime(2025, 2, 7, 9)
        self.timeout = timedelta(minutes=2)

    def __enter__(self):
        super().__enter__()
        if not self.data:
            self.logger.warning("Try to get the broken data back.")
            try:
                self.data.get_broken()
            except BotException:
                self.logger.warning("There isn't broken data to reload.")
        if not self.data:
            self.logger.warning("Try to get the deprecated data back.")
            try:
                self.data.get_deprecated()
            except BotException:
                self.logger.warning("There isn't deprecated data to reload.")
        if not self.data or self.data_outdated():
            self.data.assign_dict({"checked": {}, "authors": {}})
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
            author_dict = self.get_page_infos(page.text)
            author_dict["title"] = clean_lemma
            self.enrich_author_dict(author_dict, page)
            self.data["authors"][lemma] = author_dict
            self.data["checked"][lemma] = datetime.now().strftime("%Y%m%d%H%M%S")
            if (idx + 10 > unprocessed_lemmas) and self._watchdog():
                break

    @staticmethod
    def _strip_spaces(raw_string: str):
        return _SPACE_REGEX.subn(raw_string.strip(), " ")[0]

    def get_page_infos(self, text: str) -> AuthorDict:
        template_finder = TemplateFinder(text)
        try:
            personendaten = template_finder.get_positions("Personendaten")
        except TemplateFinderException as error:
            raise ValueError("Error in processing Personendaten template.") from error
        if len(personendaten) != 1:
            raise ValueError("No or more then one Personendaten template found.")
        template_extractor = TemplateHandler(personendaten[0]["text"])
        author_dict: AuthorDict = {}
        self.get_single_page_info("first_name", "VORNAMEN", template_extractor, author_dict)
        self.get_single_page_info("last_name", "NACHNAME", template_extractor, author_dict)
        self.get_single_page_info("birth", "GEBURTSDATUM", template_extractor, author_dict)
        self.get_single_page_info("death", "STERBEDATUM", template_extractor, author_dict)
        self.get_single_page_info("description", "KURZBESCHREIBUNG", template_extractor, author_dict)
        self.get_single_page_info("sortkey", "SORTIERUNG", template_extractor, author_dict)
        return author_dict

    def get_single_page_info(self, info: AuthorInfos, template_str: str, extractor: TemplateHandler,
                             author_dict: AuthorDict):
        try:
            template_value = self._strip_spaces(extractor.get_parameter(template_str)["value"])
        except TemplateHandlerException:
            return
        if template_value:
            author_dict[info] = template_value

    def get_lemma_list(self) -> Tuple[list[str], int]:
        searcher = PetScan()
        searcher.add_namespace(0)  # search in main namespace
        searcher.add_positive_category("Autoren")
        searcher.add_yes_template("Personendaten")
        return searcher.get_combined_lemma_list(self.data["checked"], timeframe=72)

    def enrich_author_dict(self, author_dict: AuthorDict, page: Page):
        with suppress(NoPageError):
            data_item = page.data_item()
            if "first_name" not in author_dict and "last_name" not in author_dict:
                author_dict.pop("first_name", None)
                author_dict.pop("last_name", None)
                claim = self.get_highest_claim(data_item, "P735")
                value = self.get_value_from_claim(claim)
                if value:
                    author_dict["first_name"] = value
                claim = self.get_highest_claim(data_item, "P734")
                value = self.get_value_from_claim(claim)
                if value:
                    author_dict["last_name"] = value
            if "birth" not in author_dict:
                claim = self.get_highest_claim(data_item, "P569")
                value = self.get_value_from_claim(claim)
                if value:
                    author_dict["birth"] = value
                else:
                    author_dict["birth"] = ""
            if "death" not in author_dict:
                claim = self.get_highest_claim(data_item, "P570")
                value = self.get_value_from_claim(claim)
                if value:
                    author_dict["death"] = value
                else:
                    author_dict["death"] = ""
            if "description" not in author_dict:
                try:
                    author_dict["description"] = data_item.get()["descriptions"]["de"]
                except KeyError:
                    author_dict["description"] = ""
        if "sortkey" not in author_dict:
            if "last_name" not in author_dict:
                sortkey = author_dict["first_name"]
            elif "first_name" not in author_dict:
                sortkey = author_dict["last_name"]
            else:
                sortkey = \
                    author_dict["last_name"] + ", " + author_dict["first_name"]
            sortkey = sortkey.replace("von ", "")
            author_dict["sortkey"] = sortkey

    @staticmethod
    def get_highest_claim(data_item: ItemPage, property_str: str) -> Optional[Claim]:
        try:
            claims: list[Claim] = data_item.text["claims"][property_str]
        except KeyError:
            return None
        filtered_claims = []
        for claim in claims:
            if claim.rank == "normal":
                filtered_claims.append(claim)
            elif claim.rank == "preferred":
                return claim
        if not filtered_claims:
            return None
        return filtered_claims[0]

    @staticmethod
    def get_value_from_claim(claim: Optional[Claim]) -> Optional[str]:
        if not claim:
            return None
        # handling first_- and last_name
        if claim.type == "wikibase-item":
            target = claim.getTarget()
            if target:
                with suppress(KeyError):
                    return str(claim.getTarget().get()["labels"]["de"])
                with suppress(KeyError):
                    return str(claim.getTarget().get()["labels"]["en"])
            return None
        # handling birth and death
        if claim.type == "time":
            claim_date = claim.getTarget()
            if not claim_date:
                date_from_claim = None
            elif claim_date.precision < 7:
                date_from_claim = None
            elif claim_date.precision < 8:
                date_from_claim = str(int(ceil(float(claim_date.year) / 100.0))) + ". Jh."
            elif claim_date.precision < 10:
                date_from_claim = str(claim_date.year)
            elif claim_date.precision < 11:
                date_from_claim = number_to_month[claim_date.month] + " " + str(claim_date.year)
            else:
                date_from_claim = f"{claim_date.day}. " \
                                  f"{number_to_month[claim_date.month]} " \
                                  f"{claim_date.year}"
            if date_from_claim:
                if re.search("-", date_from_claim):
                    date_from_claim = date_from_claim.replace("-", "") + " v. Chr."
                return date_from_claim
        return None

    def sort_to_list(self) -> list[AuthorDict]:
        author_list = []
        for author in self.data["authors"].values():
            author = deepcopy(author)
            author["birth_sort"] = str(DateConversion(author["birth"]))
            author["death_sort"] = str(DateConversion(author["death"]))
            author_list.append(author)
        return sorted(author_list, key=lambda author_dict: (author_dict["sortkey"], author_dict["birth_sort"]))

    def print_author_list(self, author_list: list[AuthorDict]) -> str:
        start_of_run = self.status.current_run.start_time
        string_list = []
        string_list.append(f"Diese Liste der Autoren enthält alle {len(self.data['authors'])}<ref>Stand: "
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
