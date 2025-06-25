import re
from contextlib import suppress
from datetime import timedelta, datetime

import pywikibot
from pywikibot import Site, Page

from tools.bots import BotException
from tools.bots.cloud.cloud_bot import CloudBot
from tools.petscan import PetScan, get_processed_time
from tools import has_korrigiert_category, save_if_changed, add_category


class Finisher(CloudBot):
    """Wikisource has the concept of pages (namespace "Seite") and lemmas (main namespace, no prefix).
    Lemmas can include pages. This is called proofread version 2 (PR2). If an editor finishes the proofreading of a
    page it can happen, that they forget to also change the status of the lemma, which include the page. This bot
    targets lemmas, which include 100% proofread pages, but are left in the category "Korrigiert", and tries to move
    them to the category "Fertig"."""

    def __init__(self, wiki: Site = None, debug: bool = True, log_to_screen: bool = True, log_to_wiki: bool = True):
        CloudBot.__init__(self, wiki, debug, log_to_screen, log_to_wiki)
        self.timeout: timedelta = timedelta(minutes=4)
        self.proofread_pages_set = set()

    def __enter__(self):
        super().__enter__()
        if not self.data:
            self.logger.warning("Try to get the deprecated data back.")
            try:
                self.data.get_deprecated()
            except BotException:
                self.logger.warning("There isn't deprecated data to reload.")
        return self

    def _get_proofread_pages_searcher(self) -> PetScan:
        searcher = PetScan()
        searcher.add_positive_category("Fertig")
        searcher.add_namespace("Seite")
        searcher.set_timeout(120)
        return searcher

    def _get_proofread_pages(self) -> set[str]:
        # this produces a set with all pages, which are proofread. It serves as a quick tool to check if a page is
        # proofread.
        proofread_list = self._get_proofread_pages_searcher().run()
        return {lemma["title"] for lemma in proofread_list}

    def _get_checked_lemmas_from_petscan(self) -> list[str]:
        # fetch all lemmas from the category "Korrigiert" (no pages from the namespace "Seite"),
        # they are potential candidates for the finisher
        searcher = PetScan()
        searcher.add_positive_category("Korrigiert")
        searcher.add_namespace("Article")
        searcher.set_timeout(120)
        list_checked_lemmas, _ = searcher.get_combined_lemma_list(self.data)
        # filter out lemmas from BLKÖ, RE and Zedler, those are proofread 1 concept, they don't need the finisher
        regex = re.compile(r"(BLKÖ:|RE:|Zedler:)")
        list_checked_lemmas = [item for item in list_checked_lemmas if not regex.search(item)]
        return list_checked_lemmas

    def _get_current_pages(self) -> list[str]:
        # Fetch all lemmas, which include pages, that changed to the category "Fertig" in the last 30 hours.
        searcher = self._get_proofread_pages_searcher()
        searcher.last_change_after(datetime.now() - timedelta(hours=30))
        proofread_list = searcher.run()
        return [f"Seite:{lemma['title']}" for lemma in proofread_list]

    def _get_checked_lemmas_from_current_pages(self, current_pages: list[str]) -> list[str]:
        checked_lemmas = []
        for page_name in current_pages:
            page = pywikibot.Page(self.wiki, page_name)
            pages_linking_here = list(page.backlinks())
            for page in pages_linking_here:
                if page.namespace() != 0:
                    continue
                if not has_korrigiert_category(page):
                    continue
                title = f":{page.title()}"
                if title in checked_lemmas:
                    continue
                checked_lemmas.append(title)
        return checked_lemmas

    @staticmethod
    def all_pages_fertig(pages: list[Page], proofread_pages_set: set[str]) -> bool:
        # function checks if all pages of the list have the status proofread
        for page in pages:
            if page.title(with_ns=False) not in proofread_pages_set:
                return False
        return True

    @staticmethod
    def is_overview_page(lemma: Page) -> bool:
        # if we have a lemma, that is mostly a collection of links to sub lemmas, we can't judge the proofread
        # readiness not just by the pages on the lemma page itself. This function detects (best effort) if we have such
        # page.

        # fetching all outbond links from the main namespace
        linked_pages = [page.title() for page in lemma.linkedPages() if page.namespace() in (0, 2)]
        # if some of those links contain the title of the lemma itself, it is very likely, that we have an overview
        # lemma.
        if [page for page in linked_pages if f"{lemma.title()}/" in page]:
            return True
        return False

    def task(self) -> bool:
        with self.time_step("init_proofread_dict"):
            proofread_pages_set = self._get_proofread_pages()
        with self.time_step("get_checked_lemmas_current"):
            lemmas_to_check = self._get_checked_lemmas_from_current_pages(self._get_current_pages())
        with self.time_step("get_checked_lemmas_petscan"):
            lemmas_to_check += self._get_checked_lemmas_from_petscan()
        with self.time_step("process_lemmas"):
            for idx, lemma in enumerate(lemmas_to_check):
                # time is over
                if self._watchdog():
                    break
                # register the lemma in the beginning of the processing
                self.data[lemma] = get_processed_time()
                lemma_page = Page(self.wiki, lemma)
                # lemma was loaded from storage and has changed status since then. Kick it from the storage.
                if not has_korrigiert_category(lemma_page):
                    with suppress(KeyError):
                        del self.data[lemma]
                    continue
                # if it is an overview page ... carry on
                if self.is_overview_page(lemma_page):
                    continue
                # fetch all included pages
                pages = lemma_page.templates(namespaces="Seite")
                # if there is nothing, carry on
                if not pages:
                    continue
                # if there are pages, that aren't proofread yet, carry on
                if not self.all_pages_fertig(pages, proofread_pages_set):
                    continue
                self.logger.info(f"The lemma [[{lemma}]] has only proofread pages, but isn't in the proofread cat.")
                save_if_changed(page=lemma_page,
                                text=add_category(lemma_page.text,
                                                  "Wikisource:Lemma korrigiert, alle Unterseiten fertig"),
                                change_msg="Korrekturstand des Lemmas überprüfen!")
            self.logger.info(f"{idx + 1} lemmas were processed.")
        return True


if __name__ == "__main__":
    WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
    with Finisher(wiki=WS_WIKI, debug=False, log_to_wiki=True) as bot:
        bot.run()
