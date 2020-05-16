# pylint: disable=protected-access

from testfixtures import compare

from service.ws_re.scanner.tasks.wikidata.claims.p1476_title import P1476Title
from service.ws_re.scanner.tasks.wikidata.claims.test_claim_factory import \
    BaseTestClaimFactory


class TestP1476Title(BaseTestClaimFactory):
    def test__get_claim_json_main_aritcle(self):
        re_page = self._create_mock_page(text="{{REDaten}}\ntext\n{{REAutor|Some Author.}}", title="RE:Bla")
        factory = P1476Title(re_page, None)
        claim_json = factory._get_claim_json()
        compare("Bla", claim_json[0]["mainsnak"]["datavalue"]["value"]["text"])
