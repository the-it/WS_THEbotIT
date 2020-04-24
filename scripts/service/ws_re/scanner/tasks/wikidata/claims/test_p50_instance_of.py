import pywikibot

from scripts.service.ws_re.scanner.tasks.wikidata.claims.p50_instance_of import P50Author
from scripts.service.ws_re.scanner.tasks.wikidata.claims.test_claim_factory import \
    BaseTestClaimFactory
from scripts.service.ws_re.template.re_page import RePage


class TestP50Author(BaseTestClaimFactory):
    # @skip("development")
    def test_development(self):
        WS_WIKI = pywikibot.Site(code="de", fam="wikisource", user="THEbotIT")
        lemma = pywikibot.Page(WS_WIKI, "RE:Rutilius 44")  # existing wikidata_item
        factory = P50Author(RePage(lemma))
        print(factory.get_claims_to_update(lemma.data_item()))
