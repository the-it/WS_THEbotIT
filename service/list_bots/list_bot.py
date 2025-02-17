import re
from abc import abstractmethod
from datetime import datetime
from typing import Tuple

from pywikibot import Page

from tools.bots import BotException
from tools.bots.cloud.cloud_bot import CloudBot
from tools.template_finder import TemplateFinder, TemplateFinderException
from tools.template_handler import TemplateHandler, TemplateHandlerException

_SPACE_REGEX = re.compile(r"\s+")


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
            self.data.assign_dict({})
        return self

    def task(self) -> bool:
        self.logger.info("Processing lemmas.")
        self.process_lemmas()
        self.logger.info("Sorting author list.")
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
        return True

    def process_lemmas(self):
        lemma_list, unprocessed_lemmas = self.get_lemma_list()
        for idx, lemma in enumerate(lemma_list):
            clean_lemma = lemma.strip(":").replace("_", " ")
            self.logger.debug(f"{idx + 1}/{unprocessed_lemmas} {clean_lemma}")
            page = Page(self.wiki, lemma)
            try:
                item_dict = self.get_page_infos(page)
            except ValueError:
                item_dict = {}
                self.logger.error(f"lemma {clean_lemma} was not parsed correctly.")
            self.enrich_dict(page, item_dict)
            item_dict["lemma"] = clean_lemma
            item_dict["check"] = datetime.now().strftime("%Y%m%d%H%M%S")
            self.data[lemma] = item_dict
            # if (idx + 50 > unprocessed_lemmas) and self._watchdog():
            if self._watchdog():
                break

    def get_check_dict(self):
        return {item: self.data[item]["check"] for item in self.data}

    def enrich_dict(self, page: Page, item_dict: dict[str, str]) -> None:
        pass

    def get_page_infos(self, page: Page) -> dict:
        template_finder = TemplateFinder(page.text)
        try:
            text_daten = template_finder.get_positions(self.PROPERTY_TEMPLATE)
        except TemplateFinderException as error:
            raise ValueError("Error in processing Textdaten template.") from error
        if len(text_daten) != 1:
            raise ValueError("No or more then one Textdaten template found.")
        template_extractor = TemplateHandler(text_daten[0]["text"])
        return_dict: dict[str, str] = {}
        for key, value in self.PROPERTY_MAPPING.items():
            self.get_single_page_info(key, value, template_extractor, return_dict)
        return return_dict

    def get_single_page_info(self, info: str, template_str: str, extractor: TemplateHandler,
                             info_dict: dict):
        try:
            template_value = self._strip_spaces(extractor.get_parameter(template_str)["value"])
        except TemplateHandlerException:
            return
        if template_value:
            info_dict[info] = template_value

    @staticmethod
    def _strip_spaces(raw_string: str):
        return _SPACE_REGEX.subn(raw_string.strip(), " ")[0]

    @abstractmethod
    def sort_to_list(self) -> list[dict[str, str]]:
        pass

    @abstractmethod
    def print_list(self, item_list: list[dict[str, str]]) -> str:
        pass

    @abstractmethod
    def get_lemma_list(self) -> Tuple[list[str], int]:
        pass
