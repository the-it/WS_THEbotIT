from unittest import skip

import pywikibot
from testfixtures import compare

from service.ws_re.scanner.tasks.test_base_task import TaskTestCase
from service.ws_re.scanner.tasks.wikidata.task import DATATask
from service.ws_re.template.re_page import RePage


class TestDATATask(TaskTestCase):
    @skip("just for development")
    def test_develop(self):
        WS_WIKI = pywikibot.Site(code="de", fam="wikisource", user="THEbotIT")
        # lemma = pywikibot.Page(WS_WIKI, "RE:Aba 1") # existing wikidata_item
        lemma = pywikibot.Page(WS_WIKI, "RE:Iulius 128")  # existing wikidata_item
        # print(json.dumps(lemma.data_item().toJSON(), indent=2))
        re_value = DATATask(WS_WIKI, self.logger, True).run(RePage(lemma))
        compare(re_value["success"], True)
