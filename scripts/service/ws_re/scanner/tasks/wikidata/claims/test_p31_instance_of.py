from unittest import mock

from testfixtures import compare

from scripts.service.ws_re.scanner.tasks.wikidata.claims.p31_instance_of import P31InstanceOf
from scripts.service.ws_re.scanner.tasks.wikidata.claims.test_claim_factory import \
    BaseTestClaimFactory


class TestP31InstanceOf(BaseTestClaimFactory):
    def setUp(self) -> None:
        super().setUp()
        self.factory = P31InstanceOf(self.wikidata_site_mock, self.wikisource_site_mock)

    def test__get_claim_json_main_aritcle(self):
        re_page = self._create_mock_page(text="{{REDaten}}\ntext\n{{REAutor|Some Author.}}", title="RE:Bla")
        claim_json = self.factory._get_claim_json(re_page)
        compare(13433827, claim_json["mainsnak"]["datavalue"]["value"]["numeric-id"])

    def test__get_claim_json_main_cross_reference(self):
        re_page = self._create_mock_page(text="{{REDaten|VERWEIS=ON}}\ntext\n{{REAutor|Some Author.}}", title="RE:Bla")
        claim_json = self.factory._get_claim_json(re_page)
        compare(1302249, claim_json["mainsnak"]["datavalue"]["value"]["numeric-id"])
