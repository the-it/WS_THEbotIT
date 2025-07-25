import urllib.parse
from abc import abstractmethod
from typing import Tuple

from pywikibot import Page

from service.list_bots._base import get_page_infos
from tools.bots import BotException
from tools.bots.cloud_bot import CloudBot
from tools.petscan import PetScan, get_processed_time


class ListBot(CloudBot):
    LIST_LEMMA = ""
    PROPERTY_TEMPLATE = ""
    PROPERTY_MAPPING: dict[str, str] = {}

    def __enter__(self):
        super().__enter__()
        if not self.data:
            self.logger.warning("Try to get the deprecated data back.")
            try:
                self.data.get_deprecated()
            except BotException:
                self.logger.warning("There isn't deprecated data to reload.")
        if self.data_outdated():
            self.logger.warning("The data is thrown away. It is out of date")
            self.data.clean_data()
        return self

    def task(self) -> bool:
        self.logger.info("Remove old lemmas")

        self.logger.info("Processing lemmas.")
        self.process_lemmas()
        self.logger.info("Sorting list.")
        item_list = self.sort_to_list()
        self.logger.info("Printing text.")
        new_text = self.print_list(item_list)
        author_list_page = Page(self.wiki, self.LIST_LEMMA)
        old_text = author_list_page.text
        if new_text[150:] not in old_text:  # compare all but the date
            author_list_page.text = new_text
            author_list_page.save("Die Liste wurde auf den aktuellen Stand gebracht.", bot=True)
        else:
            self.logger.info("Heute gab es keine Änderungen, daher wird die Seite nicht überschrieben.")
        self.logger.info("Post Infos.")
        self.post_infos()
        return True

    def get_page_infos(self, page) -> dict[str, str]:
        return get_page_infos(page.text, self.PROPERTY_TEMPLATE, self.PROPERTY_MAPPING)

    def process_lemmas(self):
        self.remove_old_lemmas()
        lemma_list, unprocessed_lemmas = self.get_combined_lemma_list()
        for idx, lemma in enumerate(lemma_list):
            clean_lemma = lemma.strip(":").replace("_", " ")
            self.logger.debug(f"{idx + 1}/{unprocessed_lemmas} "
                              f"https://de.wikisource.org/wiki/{urllib.parse.quote(clean_lemma)}")
            page = Page(self.wiki, lemma)
            try:
                item_dict = self.get_page_infos(page)
            except ValueError:
                item_dict = {}
                self.logger.error(f"lemma {clean_lemma} was not parsed correctly.")
            item_dict["lemma"] = clean_lemma
            self.enrich_dict(page, item_dict)
            item_dict["check"] = get_processed_time()
            self.data[lemma] = item_dict
            if (idx - 50 > unprocessed_lemmas) and self._watchdog():
                break

    def get_check_dict(self):
        return {item: self.data[item]["check"] for item in self.data}

    def enrich_dict(self, page: Page, item_dict: dict[str, str]) -> None:
        pass

    @abstractmethod
    def sort_to_list(self) -> list[dict[str, str]]:
        pass

    @abstractmethod
    def print_list(self, item_list: list[dict[str, str]]) -> str:
        pass

    @abstractmethod
    def get_searcher(self) -> PetScan:
        pass

    def get_combined_lemma_list(self) -> Tuple[list[str], int]:
        searcher = self.get_searcher()
        self.logger.info(f"Searching for combined lemma list with {searcher}")
        return searcher.get_combined_lemma_list(self.get_check_dict(), timeframe=72)

    def get_raw_lemma_list(self) -> list[str]:
        searcher = self.get_searcher()
        self.logger.info(f"Searching for raw lemma list with {searcher}")
        return searcher.make_plain_list(searcher.run())

    def post_infos(self):
        pass

    def remove_old_lemmas(self) -> None:
        lemmas_to_remove = set(self.data.keys()).difference(set(self.get_raw_lemma_list()))
        for key in lemmas_to_remove:
            del self.data[key]
