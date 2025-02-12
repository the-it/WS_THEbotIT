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

_SPACE_REGEX = re.compile(r"\s+")

class PoemList(CloudBot):
    def __init__(self, wiki: Site = None, debug: bool = True, log_to_screen: bool = True, log_to_wiki: bool = True):
        super().__init__(wiki, debug, log_to_screen, log_to_wiki)
        self.new_data_model = datetime(2025, 2, 10, 23)
        self.timeout = timedelta(minutes=1)

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
        author_list_page = Page(self.wiki, "Liste der Gedichte/New")
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
            poem_dict = self.get_page_infos(page.text)
            poem_dict["lemma"] = clean_lemma
            poem_dict["check"] = datetime.now().strftime("%Y%m%d%H%M%S")
            self.data[lemma] = poem_dict

    def get_check_dict(self):
        return {poem: self.data[poem]["check"] for poem in self.data}

    def get_lemma_list(self) -> Tuple[list[str], int]:
        searcher = PetScan()
        searcher.add_namespace(0)  # search in main namespace
        searcher.add_positive_category("Gedicht")
        searcher.set_search_depth(3)
        self.logger.info(f"Searching for lemmas with {searcher}")
        return searcher.get_combined_lemma_list(self.get_check_dict(), timeframe=72)

    def get_page_infos(self, text) -> PoemDict:
        template_finder = TemplateFinder(text)
        try:
            text_daten = template_finder.get_positions("Textdaten")
        except TemplateFinderException as error:
            raise ValueError("Error in processing Textdaten template.") from error
        if len(text_daten) != 1:
            raise ValueError("No or more then one Textdaten template found.")
        template_extractor = TemplateHandler(text_daten[0]["text"])
        poem_dict: PoemDict = {}
        self.get_single_page_info("title", "TITEL", template_extractor, poem_dict)
        self.get_single_page_info("author", "AUTOR", template_extractor, poem_dict)
        self.get_single_page_info("creation", "ENTSTEHUNGSJAHR", template_extractor, poem_dict)
        self.get_single_page_info("publish", "ERSCHEINUNGSJAHR", template_extractor, poem_dict)
        self.get_single_page_info("proofread", "BEARBEITUNGSSTAND", template_extractor, poem_dict)
        self.get_single_page_info("sortkey", "SORTIERUNG", template_extractor, poem_dict)
        return poem_dict

    @staticmethod
    def _strip_spaces(raw_string: str):
        return _SPACE_REGEX.subn(raw_string.strip(), " ")[0]

    def get_single_page_info(self, info: PoemInfos, template_str: str, extractor: TemplateHandler,
                             poem_dict: PoemDict):
        try:
            template_value = self._strip_spaces(extractor.get_parameter(template_str)["value"])
        except TemplateHandlerException:
            return
        if template_value:
            poem_dict[info] = template_value


if __name__ == "__main__":
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    with PoemList(wiki=WS_WIKI, debug=True) as bot:
        bot.run()
