# pylint: disable=protected-access

from testfixtures import compare

from service.ws_re.scanner.tasks.wikidata.claims.p361_part_of import P361PartOf
from service.ws_re.scanner.tasks.wikidata.claims.test_claim_factory import \
    BaseTestClaimFactory


class TestP361PartOf(BaseTestClaimFactory):
    def test__get_claim_json(self):
        re_page = self._create_mock_page(text="{{REDaten}}\ntext\n{{REAutor|Some Author.}}", title="RE:Bla")
        factory = P361PartOf(re_page, None)
        claim_json = factory._get_claim_json()
        compare(1138524, claim_json[0]["mainsnak"]["datavalue"]["value"]["numeric-id"])
