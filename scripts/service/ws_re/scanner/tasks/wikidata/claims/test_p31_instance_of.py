from testfixtures import compare

from scripts.service.ws_re.scanner.tasks.wikidata.claims.p31_instance_of import P31InstanceOf
from scripts.service.ws_re.scanner.tasks.wikidata.claims.test_claim_factory import \
    BaseTestClaimFactory
from testfixtures import compare

from scripts.service.ws_re.scanner.tasks.wikidata.claims.p31_instance_of import P31InstanceOf
from scripts.service.ws_re.scanner.tasks.wikidata.claims.test_claim_factory import \
    BaseTestClaimFactory


class TestP31InstanceOf(BaseTestClaimFactory):
    def test__get_claim_json_main_aritcle(self):
        re_page = self._create_mock_page(text="{{REDaten}}\ntext\n{{REAutor|Some Author.}}", title="RE:Bla")
        factory = P31InstanceOf(re_page)
        claim_json = factory._get_claim_json()
        compare(13433827, claim_json["mainsnak"]["datavalue"]["value"]["numeric-id"])

    def test__get_claim_json_main_cross_reference(self):
        re_page = self._create_mock_page(text="{{REDaten|VERWEIS=ON}}\ntext\n{{REAutor|Some Author.}}", title="RE:Bla")
        factory = P31InstanceOf(re_page)
        claim_json = factory._get_claim_json()
        compare(1302249, claim_json["mainsnak"]["datavalue"]["value"]["numeric-id"])
