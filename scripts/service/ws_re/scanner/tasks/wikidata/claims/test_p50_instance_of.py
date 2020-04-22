import pywikibot
from testfixtures import compare

from scripts.service.ws_re.scanner.tasks.wikidata.claims.p50_instance_of import P50Author
from scripts.service.ws_re.scanner.tasks.wikidata.claims.test_claim_factory import \
    BaseTestClaimFactory
from scripts.service.ws_re.template.re_page import RePage


class TestP50Author(BaseTestClaimFactory):
    def setUp(self) -> None:
        super().setUp()
        self.factory = P50Author(self.wikidata_site_mock, self.wikisource_site_mock)

    #@skip("development")
    def test_development(self):
        WS_WIKI = pywikibot.Site(code="de", fam="wikisource", user="THEbotIT")
        WD_WIKI = pywikibot.Site(code="wikidata", fam="wikidata", user="THEbotIT")
        lemma = pywikibot.Page(WS_WIKI, "RE:Rutilius 44")  # existing wikidata_item
        factory = P50Author(WD_WIKI, WS_WIKI)
        print(factory.get_claims_to_update(RePage(lemma), lemma.data_item()))

    def test__get_claim_json_main_aritcle(self):
        re_page = self._create_mock_page(text="{{REDaten}}\ntext\n{{REAutor|Some Author.}}", title="RE:Bla")
        claim_json = self.factory._get_claim_json(re_page)
        compare(13433827, claim_json["mainsnak"]["datavalue"]["value"]["numeric-id"])

    def test__get_claim_json_main_cross_reference(self):
        re_page = self._create_mock_page(text="{{REDaten|VERWEIS=ON}}\ntext\n{{REAutor|Some Author.}}", title="RE:Bla")
        claim_json = self.factory._get_claim_json(re_page)
        compare(1302249, claim_json["mainsnak"]["datavalue"]["value"]["numeric-id"])
