import os
import re
from datetime import datetime
from pathlib import Path
from typing import Mapping, List, Tuple, Dict, Any

import pywikibot
from git import Repo
from github import Github

from scripts.service.ws_re.data_types import Article
from scripts.service.ws_re.register import Registers, AuthorCrawler, RegisterException
from scripts.service.ws_re.scanner_tasks import ReScannerTask
from tools import fetch_text_from_wiki_site
from tools.bots import WikiLogger


class SCANTask(ReScannerTask):
    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        super().__init__(wiki, logger, debug)
        self.registers = Registers()
        self._strategies = {}  # type: Dict[str, List[str]]

    def task(self):
        self._fetch_from_article_list()

    def finish_task(self):
        super().finish_task()
        for strategy in self._strategies:
            self.logger.info(f"STRATEGY_{strategy}: {len(self._strategies[strategy])}")
            self.logger.info(f"{self._strategies[strategy]}")
        self.logger.info("Fetch changes for the authors.")
        authors = self.registers.authors
        authors.set_mappings(self._fetch_mapping())
        authors.set_author(self._fetch_author_infos())
        self.logger.info("Persist the register data.")
        self.registers.persist()
        self._push_changes()

    def _fetch_author_infos(self) -> Mapping:
        text = fetch_text_from_wiki_site(self.wiki,
                                         "Paulys Realencyclopädie der classischen "
                                         "Altertumswissenschaft/Autoren")
        return AuthorCrawler.get_authors(text)

    def _fetch_mapping(self) -> Mapping:
        text = fetch_text_from_wiki_site(self.wiki, "Modul:RE/Autoren")
        return AuthorCrawler.get_mapping(text)

    @staticmethod
    def _fetch_wp_link(article_list: List[Article]) -> Tuple[Dict[str, Any], List[str]]:
        article = article_list[0]
        wp_link = article["WIKIPEDIA"].value
        if wp_link:
            return {"wp_link": f"w:de:{wp_link}"}, []
        return {}, ["wp_link"]

    @staticmethod
    def _fetch_ws_link(article_list: List[Article]) -> Tuple[Dict[str, Any], List[str]]:
        article = article_list[0]
        wp_link = article["WIKISOURCE"].value
        if wp_link:
            return {"ws_link": f"s:de:{wp_link}"}, []
        return {}, ["ws_link"]

    @staticmethod
    def _fetch_sort_key(article_list: List[Article]) -> Tuple[Dict[str, Any], List[str]]:
        article = article_list[0]
        sort_key = article["SORTIERUNG"].value
        if sort_key:
            return {"sort_key": sort_key}, []
        return {}, ["sort_key"]

    def _fetch_lemma(self, _) -> Tuple[Dict[str, Any], List[str]]:  # pylint: disable=unused-argument
        return {"lemma": self.re_page.lemma_without_prefix}, []

    _REGEX_REDIRECT = re.compile(r"[sS]\..*?(?:\[\[RE:|\{\{RE siehe\|)([^\|\}]+)")

    def _fetch_redirect(self, article_list: List[Article]) -> Tuple[Dict[str, Any], List[str]]:
        article = article_list[0]
        redirect = article["VERWEIS"].value
        if redirect:
            match = self._REGEX_REDIRECT.search(article.text)
            if match:
                redirect = match.group(1)
            return {"redirect": redirect}, []
        return {}, ["redirect"]

    @staticmethod
    def _fetch_previous(article_list: List[Article]) -> Tuple[Dict[str, Any], List[str]]:
        article = article_list[0]
        previous = article["VORGÄNGER"].value
        if previous and previous != "OFF":
            return {"previous": previous}, []
        return {}, ["previous"]

    @staticmethod
    def _fetch_next(article_list: List[Article]) -> Tuple[Dict[str, Any], List[str]]:
        article = article_list[0]
        next_lemma = article["NACHFOLGER"].value
        if next_lemma and next_lemma != "OFF":
            return {"next": next_lemma}, []
        return {}, ["next"]

    def _fetch_from_article_list(self):
        function_list_properties = (self._fetch_wp_link, self._fetch_ws_link, self._fetch_sort_key, self._fetch_lemma,
                                    self._fetch_redirect, self._fetch_previous, self._fetch_next)
        for article_list in self.re_page.splitted_article_list:
            # fetch from properties
            if isinstance(article_list[0], Article):
                update_dict = {}
                delete_list = []
                for fetch_function in function_list_properties:
                    function_dict, function_list = fetch_function(article_list)
                    update_dict.update(function_dict)
                    delete_list += function_list
                band_info = article_list[0]["BAND"].value
                register = self.registers.volumes[band_info]
                if register:
                    try:
                        strategy = register.update_lemma(update_dict, delete_list)
                        self._write_strategy_statistic(strategy, update_dict, band_info)
                    except RegisterException as error:
                        self.logger.error(f"No available Lemma in Registers for issue {band_info} "
                                          f"and lemma {self.re_page.lemma_as_link}. "
                                          f"Reason is: {error.args[0]}")

    def _write_strategy_statistic(self, strategy: str, update_dict: Dict, issue_no: str):
        entry = f"{update_dict['lemma']}/{issue_no}"
        if strategy in self._strategies:
            self._strategies[strategy].append(entry)
        else:
            self._strategies[strategy] = [entry]

    def _push_changes(self):
        repo = Repo(search_parent_directories=True)
        if repo.index.diff(None):
            master = repo.active_branch
            now = datetime.now().strftime("%y%m%d_%H%M%S")
            branch_name = f"{now}_updating_registers"
            self.logger.info(f"Pushing changes to \"{branch_name}\"")
            repo.git.checkout("-b", branch_name)
            repo.git.add(str(Path(__file__).parent.joinpath("register")))
            repo.index.commit(f"Updating the register at {now}")
            repo.git.push("origin", repo.active_branch.name)
            repo.git.checkout(master.name)
            if "GITHUB_USER" in os.environ:  # pragma: no cover
                self.logger.info(f"Opening Pullrequest for \"{branch_name}\"")
                self._open_pullrequest(branch_name)
            else:
                self.logger.error("No env variable GITHUB_USER")
        else:
            self.logger.info("No Changes to push today.")

    @staticmethod
    def _open_pullrequest(branch_name: str):  # pragma: no cover
        github = Github(os.environ["GITHUB_USER"], os.environ["GITHUB_PASSWORD"])
        github_repo = github.get_repo("the-it/WS_THEbotIT")
        github_repo.create_pull(title=branch_name,
                                head=branch_name,
                                base="master",
                                body="Update registers",
                                maintainer_can_modify=True)
