import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict

import pywikibot
from git import Repo
from github import Github

from scripts.service.ws_re.register.author import AuthorCrawler, AuthorDict, CrawlerDict
from scripts.service.ws_re.register.base import RegisterException
from scripts.service.ws_re.register.lemma import LemmaDict, ChapterDict
from scripts.service.ws_re.register.registers import Registers
from scripts.service.ws_re.register.updater import Updater, RemoveList
from scripts.service.ws_re.scanner.tasks.base_task import ReScannerTask
from scripts.service.ws_re.template.article import Article
from tools import fetch_text_from_wiki_site
from tools.bots import WikiLogger


class SCANTask(ReScannerTask):
    def __init__(self, wiki: pywikibot.Site, logger: WikiLogger, debug: bool = True):
        super().__init__(wiki, logger, debug)
        self.registers = Registers()
        self._strategies: Dict[str, List[str]] = {}

    def task(self):
        self._process_from_article_list()

    def finish_task(self):
        super().finish_task()
        for strategy in self._strategies:
            self.logger.info(f"STRATEGY_{strategy}: {len(self._strategies[strategy])}")
            if strategy != "update_lemma_by_name":
                self.logger.info(f"{self._strategies[strategy]}")
        self.logger.info("Fetch changes for the authors.")
        authors = self.registers.authors
        authors.set_mappings(self._get_author_mapping())
        authors.set_author(self._process_author_infos())
        self.logger.info("Persist the author data.")
        authors.persist()
        self.logger.info("Persist the register data.")
        self.registers.persist()
        self._push_changes()

    def _process_author_infos(self) -> Dict[str, AuthorDict]:
        text = fetch_text_from_wiki_site(self.wiki,
                                         "Paulys Realencyclopädie der classischen "
                                         "Altertumswissenschaft/Autoren")
        return AuthorCrawler.get_authors(text)

    def _get_author_mapping(self) -> CrawlerDict:
        text = fetch_text_from_wiki_site(self.wiki, "Modul:RE/Autoren")
        return AuthorCrawler.get_mapping(text)

    @staticmethod
    def _fetch_wp_link(article_list: List[Article]) -> Tuple[LemmaDict, RemoveList]:
        article = article_list[0]
        wp_link = article["WIKIPEDIA"].value
        if wp_link:
            return {"wp_link": f"w:de:{wp_link}"}, []
        return {}, ["wp_link"]

    @staticmethod
    def _fetch_ws_link(article_list: List[Article]) -> Tuple[LemmaDict, RemoveList]:
        article = article_list[0]
        wp_link = article["WIKISOURCE"].value
        if wp_link:
            return {"ws_link": f"s:de:{wp_link}"}, []
        return {}, ["ws_link"]

    @staticmethod
    def _fetch_sort_key(article_list: List[Article]) -> Tuple[LemmaDict, RemoveList]:
        article = article_list[0]
        sort_key = article["SORTIERUNG"].value
        if sort_key:
            return {"sort_key": sort_key}, []
        return {}, ["sort_key"]

    def _fetch_lemma(self, _) -> Tuple[LemmaDict, RemoveList]:  # pylint: disable=unused-argument
        return {"lemma": self.re_page.lemma_without_prefix}, []

    _REGEX_REDIRECT = re.compile(r"[sS]\..*?(?:\[\[RE:|\{\{RE siehe\|)([^\|\}]+)")

    def _fetch_redirect(self, article_list: List[Article]) -> Tuple[LemmaDict, RemoveList]:
        article = article_list[0]
        redirect = article["VERWEIS"].value
        if redirect:
            match = self._REGEX_REDIRECT.search(article.text)
            if match:
                redirect = match.group(1)
            return {"redirect": redirect}, []
        return {}, ["redirect"]

    @staticmethod
    def _fetch_previous(article_list: List[Article]) -> Tuple[LemmaDict, RemoveList]:
        article = article_list[0]
        previous = article["VORGÄNGER"].value
        if previous and previous != "OFF":
            return {"previous": previous}, []
        return {}, ["previous"]

    @staticmethod
    def _fetch_next(article_list: List[Article]) -> Tuple[LemmaDict, RemoveList]:
        article = article_list[0]
        next_lemma = article["NACHFOLGER"].value
        if next_lemma and next_lemma != "OFF":
            return {"next": next_lemma}, []
        return {}, ["next"]

    def _fetch_pages(self, article_list: List[Article]) -> Tuple[LemmaDict, RemoveList]:
        # if there is something outside an article ignore it
        article_list = [article for article in article_list if isinstance(article, Article)]
        if self.re_page.complex_construction:
            self.logger.error(f"The construct of {self.re_page.lemma_without_prefix} is too complex, can't analyse.")
            return {}, []
        if len(article_list) == 1:
            chapter_dict = self._analyse_simple_article_list(article_list)
            if chapter_dict:
                return {"chapters": [chapter_dict]}, []
            return {}, []
        return {"chapters": self._analyse_complex_article_list(article_list)}, []

    def _analyse_simple_article_list(self, article_list: List[Article]) -> ChapterDict:
        article = article_list[0]
        try:
            spalte_start = int(article["SPALTE_START"].value)
        except ValueError:
            self.logger.error(f"{self.re_page.lemma_without_prefix} has no correct start column.")
            return {}
        spalte_end = article["SPALTE_END"].value
        if spalte_end and spalte_end != "OFF":
            spalte_end = int(spalte_end)
        else:
            spalte_end = spalte_start
        single_article_dict: ChapterDict = {"start": spalte_start, "end": spalte_end}
        author = article.author[0]
        if author.lower().strip() != "off":
            single_article_dict["author"] = author
        return single_article_dict

    def _analyse_complex_article_list(self, article_list: List[Article]) -> List[ChapterDict]:
        simple_dict = self._analyse_simple_article_list(article_list)
        article_start = int(simple_dict["start"])
        chapter_list: List[ChapterDict] = []
        for article in article_list:
            # if there will be no findings of the regex, the article continues on the next page as the predecessor
            start: int = article_start
            end: int = article_start
            findings = list(re.finditer(r"\{\{Seite\|(\d{1,4})", article.text))
            if findings:
                first_finding = findings[0]
                start = int(first_finding.group(1))
                if first_finding.start(0) > 0:
                    start -= 1
                end = int(findings[-1].group(1))
            if article is article_list[-1]:
                end = int(simple_dict["end"])
            chapter_list.append({"start": start, "end": end, "author": article.author[0]})
            article_start = end
        return chapter_list

    def _process_from_article_list(self):
        function_list_properties = []
        for item in dir(self):
            if "_fetch" in item:
                function_list_properties.append(getattr(self, item))
        issues_in_articles = set()
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
                self_supplement = band_info in issues_in_articles
                issues_in_articles.add(band_info)
                self._update_lemma(band_info, delete_list, self_supplement, update_dict)

    def _update_lemma(self, band_info: str, delete_list: RemoveList, self_supplement: bool, update_dict: LemmaDict):
        register = self.registers.volumes[band_info]
        if register:
            try:
                with Updater(register) as updater:
                    strategy = updater.update_lemma(update_dict, delete_list, self_supplement)
                self._write_strategy_statistic(strategy, update_dict, band_info)
            except RegisterException as error:
                self.logger.error(f"No available Lemma in Registers for issue {band_info} "
                                  f"and lemma {self.re_page.lemma_as_link}. "
                                  f"Reason is: {error.args[0]}")

    def _write_strategy_statistic(self, strategy: str, update_dict: LemmaDict, issue_no: str):
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
            repo.git.add(str(Path(__file__).parent.parent.parent.joinpath("register").joinpath("data")))
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
