# pylint: skip-file
import json
from time import sleep
from unittest.case import TestCase, skipUnless

import pywikibot

from service.ws_re.scanner.tasks.wikidata.claims.p6216_copyright_status import P6216CopyrightStatus
from service.ws_re.scanner.tasks.wikidata.test import wikidata_test
from service.ws_re.template.re_page import RePage
from tools import REAL_WIKI_TEST



@skipUnless(REAL_WIKI_TEST, "only execute in integration test")
class TestDev(TestCase):
    @wikidata_test
    def test_development(self):
        WS_WIKI = pywikibot.Site(code="de", fam="wikisource", user="THEbotIT")
        lemma = pywikibot.Page(WS_WIKI, "RE:Rutilius 44")  # existing wikidata_item
        factory = P6216CopyrightStatus(RePage(lemma), None)
        sleep(10)
        print(json.dumps(factory._get_claim_json(), indent=2))
