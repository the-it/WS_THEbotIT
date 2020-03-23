import pywikibot

from scripts.service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from scripts.service.ws_re.scanner.tasks.wikidata import DATATask
from scripts.service.ws_re.template.re_page import RePage


class TestDATATask(TaskTestCase):
    def test_develop(self):
        WS_WIKI = pywikibot.Site(code="de", fam="wikisource", user="THEbotIT")
        # lemma = pywikibot.Page(WS_WIKI, "RE:Aba 1") # existing wikidata_item
        lemma = pywikibot.Page(WS_WIKI, "RE:Rutilius 44")  # existing wikidata_item
        DATATask(WS_WIKI, self.logger, True).run(RePage(lemma))
