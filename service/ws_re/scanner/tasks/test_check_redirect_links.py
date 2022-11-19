# pylint: disable=protected-access
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
        replaced_text = task.replace_redirect_links(text, redirect, target)
        compare(expect, replaced_text)

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
