from unittest.case import TestCase

import pywikibot

from scripts.service.ws_re.template.re_page import RePage


class TestDev(TestCase):
    # @skip("development")
    def test_development(self):
        WS_WIKI = pywikibot.Site(code="de", fam="wikisource", user="THEbotIT")
        lemma = pywikibot.Page(WS_WIKI, "RE:Rutilius 44")  # existing wikidata_item
        factory = P50Author(RePage(lemma))
        print(factory.get_claims_to_update(lemma.data_item()))
