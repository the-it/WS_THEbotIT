# pylint: disable=protected-access
from unittest import mock

import pywikibot
from ddt import ddt, file_data
from pywikibot import Site
from testfixtures import compare

from service.ws_re.scanner.tasks.check_redirect_links import CHRETask
from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.template.re_page import RePage
from tools.test import real_wiki_test


class TestCHRETaskRealWiki(TaskTestCase):
    @real_wiki_test
    def test_get_backlinks(self):
        WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
        task = CHRETask(WS_WIKI, self.logger)
        compare(["Benutzer:S8w4/Spielwiese/Lemmata06kurz",
                "Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/PD 2013"],
                task.get_backlinks(pywikibot.Page(WS_WIKI, "RE:ho epi bomo hiereus")))

    @real_wiki_test
    def test_integration(self):
        WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
        task = CHRETask(WS_WIKI, self.logger)
        task.re_page = RePage(pywikibot.Page(WS_WIKI, "RE:Ulpius 1a"))
        task.task()


@ddt
class TestCHRETaskUnittests(TaskTestCase):
    @file_data("test_data/test_check_redirect_links.yml")
    def test_replace_redirect_links(self, text, redirect, target, expect):
        task = CHRETask(None, self.logger)
        replaced_text = task.replace_redirect_links(text, [redirect], target)
        compare(expect, replaced_text)

    @staticmethod
    def _redirect_mock(title, redirects=None):
        page = mock.Mock(spec=pywikibot.Page)
        page.title.return_value = title
        page.redirects.return_value = redirects or []
        return page

    def test_collect_redirect_chain_follows_chain(self):
        # RE:A -> RE:B -> RE:Target; get_redirects() only yields the direct hop RE:B
        leaf = self._redirect_mock("RE:A")
        direct = self._redirect_mock("RE:B", redirects=[leaf])
        task = CHRETask(None, self.logger)
        task.re_page = mock.Mock()
        task.re_page.get_redirects.return_value = [direct]
        compare(["RE:B", "RE:A"], [page.title() for page in task.collect_redirect_chain()])

    def test_collect_redirect_chain_handles_cycle(self):
        # RE:A and RE:B redirect to each other; the walk must terminate
        direct = self._redirect_mock("RE:B")
        leaf = self._redirect_mock("RE:A", redirects=[direct])
        direct.redirects.return_value = [leaf]
        task = CHRETask(None, self.logger)
        task.re_page = mock.Mock()
        task.re_page.get_redirects.return_value = [direct]
        compare(["RE:B", "RE:A"], [page.title() for page in task.collect_redirect_chain()])

    def test_replace_redirect_links_matches_any_chain_title(self):
        # a single page may reference different redirects of the same chain
        text = "[[RE:Alias one]]\n[[RE:Alias two|label]]\n{{RE siehe|Alias one}}\n"
        expect = "[[RE:Target]]\n[[RE:Target|label]]\n{{RE siehe|Target|Alias one}}\n"
        task = CHRETask(None, self.logger)
        compare(expect, task.replace_redirect_links(text, ["Alias one", "Alias two"], "Target"))

    def test_replace_redirect_links_prefers_longest_title(self):
        # "Ab" must not shadow "Abc" when both are in the chain
        text = "[[RE:Abc]]\n[[RE:Ab]]\n"
        expect = "[[RE:Target]]\n[[RE:Target]]\n"
        task = CHRETask(None, self.logger)
        compare(expect, task.replace_redirect_links(text, ["Ab", "Abc"], "Target"))

    def test_filter_link_list(self):
        link_list = [
            "Literatur",
            "RE:Querverweis",
            "Wikisource:RE-Werkstatt/Zeug in der Werkstatt",
            "Benutzer:S8w4/Spielwiese/Lemmata06kurz",
            "Benutzer Diskussion:S8w4",
            "Benutzer:THEbotIT/some_logging_page",
            "RE:Wartung:Strukturfehler",
            "Paulys Realencyclopädie der classischen Altertumswissenschaft/Register/PD 2013",
        ]
        task = CHRETask(None, self.logger)
        compare(["Literatur", "RE:Querverweis"], task.filter_link_list(link_list))
