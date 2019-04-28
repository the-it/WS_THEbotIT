import os
import re
from abc import abstractmethod
from datetime import timedelta, datetime
from pathlib import Path
from typing import Mapping, Tuple, Any, Dict, List

from git import Repo
from github import Github
from pywikibot import Site, Page

from scripts.service.ws_re.data_types import RePage, Article
from scripts.service.ws_re.register import Registers, AuthorCrawler, RegisterException
from tools import fetch_text_from_wiki_site
from tools.bots import WikiLogger

SUCCESS = "success"
CHANGED = "changed"


class ReScannerTask:
    def __init__(self, wiki: Site, logger: WikiLogger, debug: bool = True):
        self.wiki = wiki
        self.debug = debug
        self.logger = logger
        self.re_page = None  # type: RePage
        self.processed_pages = []
        self.timeout = timedelta(minutes=1)
        self.load_task()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    def task(self):
        pass

    def run(self, re_page: RePage):
        self.re_page = re_page
        preprocessed_hash = hash(self.re_page)
        result = {SUCCESS: False, CHANGED: False}
        try:
            self.task()
        except Exception as exception:  # pylint: disable=broad-except
            self.logger.exception("Logging a caught exception", exception)
        else:
            result[SUCCESS] = True
            self.processed_pages.append(re_page.lemma)
        if preprocessed_hash != hash(self.re_page):
            result[CHANGED] = True
        return result

    def load_task(self):
        self.logger.info(f"opening task {self.name}")

    def finish_task(self):
        self.logger.info(f"closing task {self.name}")

    @property
    def name(self):
        return re.search("([A-Z0-9]{4})[A-Za-z]*?Task", str(self.__class__)).group(1)


class ERROTask(ReScannerTask):
    def __init__(self, wiki: Site, logger: WikiLogger, debug: bool = True):
        super().__init__(wiki, logger, debug)
        self.data = []

    def task(self, lemma: str, reason: str):  # pylint: disable=arguments-differ
        self.data.append((lemma, reason))

    def _build_entry(self) -> str:
        caption = f"\n\n=={datetime.now():%Y-%m-%d}==\n\n"
        entries = []
        for item in self.data:
            entries.append(f"* [[{item[0]}]]\n** {item[1]}")
        body = "\n".join(entries)
        return caption + body

    def finish_task(self):
        if self.data:
            if not self.debug:
                page = Page(self.wiki, "RE:Wartung:Strukturfehler")
                page.text = page.text + self._build_entry()
                page.save("Neue Fehlermeldungen", botflag=True)
        super().finish_task()


class KSCHTask(ReScannerTask):
    _regex_template = re.compile(r"{{RE keine Schöpfungshöhe\|(\d\d\d\d)}}")

    def task(self):
        for re_article in self.re_page:
            if isinstance(re_article, Article):
                template_match = self._regex_template.search(re_article.text)
                if template_match:
                    re_article["TODESJAHR"].value = template_match.group(1)
                    re_article["KEINE_SCHÖPFUNGSHÖHE"].value = True
                    re_article.text = self._regex_template.sub("", re_article.text).strip()


class VERWTask(ReScannerTask):
    _basic_regex = r"\[\[Kategorie:RE:Verweisung\|?[^\]]*\]\]"
    _regex_template = re.compile(_basic_regex)
    _regex_only_template = re.compile(r"^" + _basic_regex + r"$")

    def task(self):
        for idx, re_article in enumerate(self.re_page):
            if isinstance(re_article, Article):
                template_match = self._regex_template.search(re_article.text)
                if template_match:
                    re_article["VERWEIS"].value = True
                    re_article.text = self._regex_template.sub("", re_article.text).strip()
            elif isinstance(re_article, str):
                template_match = self._regex_only_template.search(re_article)
                if template_match and idx > 0:
                    self.re_page[idx - 1]["VERWEIS"].value = True
                    self.re_page[idx] = ""
        self.re_page.clean_articles()


class TJGJTask(ReScannerTask):
    def __init__(self, wiki: Site, logger: WikiLogger, debug: bool = True):
        super().__init__(wiki, logger, debug)
        self.registers = Registers()

    def task(self):
        for article_list in self.re_page.splitted_article_list:
            if not isinstance(article_list[0], str):
                article = article_list[0]
                if article["TODESJAHR"].value == "3333":
                    author = self.registers.authors.get_author_by_mapping(article.author[0], article["BAND"].value)
                    if author:
                        if author.birth:
                            article["GEBURTSJAHR"].value = str(author.birth)
                            article["TODESJAHR"].value = ""
                    else:
                        self.logger.error(f"TJGJ: No author registered for {article.author[0]} "
                                          f"in lemma {self.re_page.lemma}")
        return True


class SCANTask(ReScannerTask):
    _LEMMAS_MAX = 500

    def __init__(self, wiki: Site, logger: WikiLogger, debug: bool = True):
        super().__init__(wiki, logger, debug)
        self.registers = Registers()
        self._register_lemmas = True
        self._lemmas_registered = 0

    def task(self):
        if self._register_lemmas:
            if self._lemmas_registered < self._LEMMAS_MAX:
                self._lemmas_registered += 1
                self._fetch_from_article_list()
            else:
                self.logger.warning(f"SCANTask reached the max lemmas to process with lemma {self.re_page.lemma}.")
                self._register_lemmas = False

    def finish_task(self):
        super().finish_task()
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

    @staticmethod
    def _fetch_redirect(article_list: List[Article]) -> Tuple[Dict[str, Any], List[str]]:
        article = article_list[0]
        redirect = article["VERWEIS"].value
        if redirect:
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
                        register.update_lemma(update_dict, delete_list)
                        continue
                    except RegisterException:
                        self.logger.error(f"No available Lemma in Registers for issue {band_info} "
                                          f"and lemma {self.re_page.lemma_as_link}")

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
