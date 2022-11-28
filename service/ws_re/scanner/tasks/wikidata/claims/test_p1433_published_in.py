# pylint: disable=protected-access

from testfixtures import compare

from service.ws_re.scanner.tasks.wikidata.claims.p1433_published_in import P1433PublishedIn
from service.ws_re.scanner.tasks.wikidata.claims.test_claim_factory import \
    BaseTestClaimFactory


class TestP1433PublishedIn(BaseTestClaimFactory):
    def test__get_claim_json_I1(self):
        re_page = self._create_mock_page(text="{{REDaten\n|BAND=I,1}}\ntext\n{{REAutor|Some Author.}}", title="RE:Bla")
        factory = P1433PublishedIn(re_page, None)
        claim_json = factory._get_claim_json()
        compare(26414644, claim_json[0]["mainsnak"]["datavalue"]["value"]["numeric-id"])

    def test__get_claim_json_R(self):
        re_page = self._create_mock_page(text="{{REDaten\n|BAND=R}}\ntext\n{{REAutor|Some Author.}}", title="RE:Bla")
        factory = P1433PublishedIn(re_page, None)
        claim_json = factory._get_claim_json()
        compare(26470176, claim_json[0]["mainsnak"]["datavalue"]["value"]["numeric-id"])
