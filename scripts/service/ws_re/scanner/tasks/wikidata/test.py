import json

import pywikibot
from testfixtures import compare

from scripts.service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from scripts.service.ws_re.scanner.tasks.wikidata import DATATask
from scripts.service.ws_re.template.re_page import RePage


class TestDATATask(TaskTestCase):
    #@skip("just for development")
    def test_develop(self):
        WS_WIKI = pywikibot.Site(code="de", fam="wikisource", user="THEbotIT")
        # lemma = pywikibot.Page(WS_WIKI, "RE:Aba 1") # existing wikidata_item
        lemma = pywikibot.Page(WS_WIKI, "RE:Rutilius 44")  # existing wikidata_item
        print(json.dumps(lemma.data_item().toJSON(), indent=2))
        re_value = DATATask(WS_WIKI, self.logger, True).run(RePage(lemma))
        compare(re_value["success"], True)

    def test_load_claim_factories(self):
        task = DATATask(None, self.logger)
        task._get_claim_classes()
