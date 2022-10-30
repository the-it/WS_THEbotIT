# pylint: disable=protected-access
import pywikibot
from pywikibot import Site

from service.ws_re.scanner.tasks.categorize_redirects import CARETask
from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.template.re_page import RePage
from tools.test import real_wiki_test


class TestCARETask(TaskTestCase):
    @real_wiki_test
    def test_integration(self):
        WS_WIKI = Site(code="de", fam="wikisource", user="THEbotIT")
        task = CARETask(WS_WIKI, self.logger)
        task.re_page = RePage(pywikibot.Page(WS_WIKI, "RE:Χαλκῆ μυῖα"))
        task.task()
