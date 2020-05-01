import json
from unittest.case import TestCase

import pywikibot

from service.ws_re.scanner.tasks.wikidata.claims.p6212_copyright_status import P6212CopyrightStatus
from service.ws_re.template.re_page import RePage


#@skip("development")
class TestDev(TestCase):
    def test_development(self):
        WS_WIKI = pywikibot.Site(code="de", fam="wikisource", user="THEbotIT")
        lemma = pywikibot.Page(WS_WIKI, "RE:Rutilius 44")  # existing wikidata_item
        factory = P6212CopyrightStatus(RePage(lemma))
        print(json.dumps( factory._get_claim_json(), indent=2))
