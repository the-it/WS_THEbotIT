import contextlib
import re
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Sequence

import pywikibot
from git import Repo

from service.ws_re.register._base import RegisterException
from service.ws_re.register._typing import ChapterDict, LemmaDict, UpdaterRemoveList
from service.ws_re.register.author_crawler import AuthorCrawler
from service.ws_re.register.registers import Registers
from service.ws_re.register.updater import Updater
from service.ws_re.scanner.tasks.base_task import ReScannerTask
from service.ws_re.template.article import Article
from tools.bots.pi import WikiLogger


class SCANTask(ReScannerTask):
    ERROR_CAT = "RE:Nicht ins Register einsortierbar"

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
        authors.set_mappings(AuthorCrawler.get_author_mapping(self.wiki))
        authors.set_author(AuthorCrawler.process_author_infos(self.wiki))
        self.logger.info("Persist the author data.")
        authors.persist()
        self.logger.info("Persist the register data.")
        self.registers.persist()
        self._push_changes()

    def _fetch_wp_link(self, article_list: List[Article]) -> Tuple[LemmaDict, UpdaterRemoveList]:
        article = article_list[0]
        if article['WIKIPEDIA'].value:
            wp_link: Optional[str] = f"w:de:{article['WIKIPEDIA'].value}"
        else:
            try:
                wp_link = self._get_link_from_wd(("dewiki", "enwiki", "frwiki", "itwiki", "eswiki", "ptwiki", "sewiki",
                                                  "cawiki", "lawiki", "arwiki", "trwiki", "elwiki"))
            except pywikibot.exceptions.MaxlagTimeoutError:
                return {}, []
        if wp_link:
            return {"wp_link": wp_link}, []
        return {}, ["wp_link"]

    def _fetch_ws_link(self, article_list: List[Article]) -> Tuple[LemmaDict, UpdaterRemoveList]:
        article = article_list[0]
        if article['WIKISOURCE'].value:
            ws_link: Optional[str] = f"s:de:{article['WIKISOURCE'].value}"
        else:
            try:
                ws_link = self._get_link_from_wd(("dewikisource", "enwikisource", "frwikisource", "itwikisource",
                                                  "eswikisource", "ptwikisource", "sewikisource", "cawikisource",
                                                  "lawikisource", "arwikisource", "trwikisource", "elwikisource"))
            except pywikibot.exceptions.MaxlagTimeoutError:
                return {}, []
        if ws_link:
            return {"ws_link": ws_link}, []
        return {}, ["ws_link"]

    def _fetch_wd_link(self, _) -> Tuple[LemmaDict, UpdaterRemoveList]:
        try:
            target = self._get_target_from_wd()
        except pywikibot.exceptions.MaxlagTimeoutError:
            return {}, []
        if target:
            return {"wd_link": f"d:{target.id}"}, []
        return {}, ["wd_link"]

    def _get_link_from_wd(self, possible_source_wikis: Sequence) -> Optional[str]:
        target = self._get_target_from_wd()
        if target:
            for sitelink in possible_source_wikis:
                with contextlib.suppress(pywikibot.exceptions.NoPage):
                    wiki_prefix = "s" if sitelink.find("wikisource") > 0 else "w"
                    link = f"{wiki_prefix}:{sitelink[0:2]}:{target.getSitelink(sitelink)}"
                    return link
        return None

    def _get_target_from_wd(self) -> Optional[pywikibot.ItemPage]:
        try:
            with contextlib.suppress(pywikibot.exceptions.NoPage):
                wp_item = self.re_page.page.data_item()
                with contextlib.suppress(KeyError):
                    return wp_item.claims["P921"][0].target
            return None
        except pywikibot.exceptions.MaxlagTimeoutError as exception:
            self.logger.debug(f"No WD target, because of timeout at {self.re_page.lemma_as_link}")
            raise exception

    @staticmethod
    def _fetch_sort_key(article_list: List[Article]) -> Tuple[LemmaDict, UpdaterRemoveList]:
        article = article_list[0]
        sort_key = str(article["SORTIERUNG"].value)
        if sort_key:
            return {"sort_key": sort_key}, []
        return {}, ["sort_key"]

    def _fetch_lemma(self, _) -> Tuple[LemmaDict, UpdaterRemoveList]:  # pylint: disable=unused-argument
        return {"lemma": self.re_page.lemma_without_prefix}, []

    _REGEX_REDIRECT = re.compile(r"[sS]\..*?(?:\[\[RE:|\{\{RE siehe\|)([^\|\}]+)")

    def _fetch_redirect(self, article_list: List[Article]) -> Tuple[LemmaDict, UpdaterRemoveList]:
        article = article_list[0]
        redirect = article["VERWEIS"].value
        if redirect:
            match = self._REGEX_REDIRECT.search(article.text)
            if match:
                redirect = match.group(1)
            return {"redirect": redirect}, []
        return {}, ["redirect"]

    @staticmethod
    def _fetch_previous(article_list: List[Article]) -> Tuple[LemmaDict, UpdaterRemoveList]:
        article = article_list[0]
        previous = str(article["VORGÄNGER"].value)
        if previous and previous != "OFF":
            return {"previous": previous}, []
        return {}, ["previous"]

    @staticmethod
    def _fetch_next(article_list: List[Article]) -> Tuple[LemmaDict, UpdaterRemoveList]:
        article = article_list[0]
        next_lemma = str(article["NACHFOLGER"].value)
        if next_lemma and next_lemma != "OFF":
            return {"next": next_lemma}, []
        return {}, ["next"]

    def _fetch_pages(self, article_list: List[Article]) -> Tuple[LemmaDict, UpdaterRemoveList]:
        # if there is something outside an article ignore it
        article_list = [article for article in article_list if isinstance(article, Article)]
        if self.re_page.complex_construction:
            self.logger.error(f"The construct of {self.re_page.lemma_as_link} "
                              f"is too complex, can't analyse.")
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
            self.logger.error(f"[[{self.re_page.lemma_without_prefix}]] has no correct start column.")
            return {}
        spalte_end_raw = article["SPALTE_END"].value
        if spalte_end_raw and spalte_end_raw != "OFF":
            spalte_end = int(spalte_end_raw)
        else:
            spalte_end = spalte_start
        single_article_dict = self._create_chapter_dict(article, spalte_end, spalte_start)
        return single_article_dict

    def _analyse_complex_article_list(self, article_list: List[Article]) -> List[ChapterDict]:
        simple_dict = self._analyse_simple_article_list(article_list)
        article_start = int(simple_dict["start"])
        chapter_list: List[ChapterDict] = []
        for article in article_list:
            # if there will be no findings of the regex, the article continues on the next page as the predecessor
            spalte_start: int = article_start
            spalte_end: int = article_start
            findings = list(re.finditer(r"\{\{Seite\|(\d{1,4})", article.text))
            if findings:
                first_finding = findings[0]
                spalte_start = int(first_finding.group(1))
                if first_finding.start(0) > 0:
                    spalte_start -= 1
                spalte_end = int(findings[-1].group(1))
            if article is article_list[-1]:
                spalte_end = int(simple_dict["end"])
            single_article_dict = self._create_chapter_dict(article, spalte_end, spalte_start)
            chapter_list.append(single_article_dict)
            article_start = spalte_end
        return chapter_list

    @staticmethod
    def _create_chapter_dict(article: Article, spalte_end: int, spalte_start: int) -> ChapterDict:
        single_article_dict: ChapterDict = {"start": spalte_start, "end": spalte_end}
        author = article.author[0]
        if author.lower().strip() != "off":
            single_article_dict["author"] = author
        return single_article_dict

    @staticmethod
    def _fetch_proof_read(article_list: List[Article]) -> Tuple[LemmaDict, UpdaterRemoveList]:
        article = article_list[0]
        proof_read = str(article["KORREKTURSTAND"].value).lower().strip()
        if article.common_free:
            if proof_read:
                if proof_read == "fertig":
                    return {"proof_read": 3}, []
                if proof_read == "korrigiert":
                    return {"proof_read": 2}, []
        return {}, ["proof_read"]

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

    def _update_lemma(self,
                      band_info: str,
                      delete_list: UpdaterRemoveList,
                      self_supplement: bool,
                      update_dict: LemmaDict):
        register = self.registers.volumes[band_info]
        if register:
            try:
                with Updater(register) as updater:
                    strategy = updater.update_lemma(update_dict, delete_list, self_supplement)
                self._write_strategy_statistic(strategy, update_dict, band_info)
                self.re_page.remove_error_category(self.ERROR_CAT)
            except RegisterException as error:
                self.logger.error(f"No available Lemma in Registers for issue {band_info} "
                                  f"and lemma {self.re_page.lemma_as_link}. "
                                  f"Reason is: {error.args[0]}")
                self.re_page.add_error_category(self.ERROR_CAT)

    def _write_strategy_statistic(self, strategy: str, update_dict: LemmaDict, issue_no: str):
        entry = f"{update_dict['lemma']}/{issue_no}"
        if strategy in self._strategies:
            self._strategies[strategy].append(entry)
        else:
            self._strategies[strategy] = [entry]

    def _push_changes(self):
        repo = Repo(search_parent_directories=True)
        if repo.index.diff(None):
            repo.git.add(str(Path(__file__).parent.parent.parent.joinpath("register").joinpath("data")))
            now = datetime.now().strftime("%y%m%d_%H%M%S")
            repo.index.commit(f"Updating the register at {now}")
            repo.git.push("origin", repo.active_branch.name)
        else:
            self.logger.info("No Changes to push today.")
