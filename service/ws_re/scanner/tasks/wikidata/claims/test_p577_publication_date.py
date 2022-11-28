# pylint: disable=protected-access

from testfixtures import compare

from service.ws_re.scanner.tasks.wikidata.claims.p577_publication_date import P577PublicationDate
from service.ws_re.scanner.tasks.wikidata.claims.test_claim_factory import \
    BaseTestClaimFactory


class TestP577PublicationDate(BaseTestClaimFactory):
    def test__get_claim_json_I1(self):
        re_page = self._create_mock_page(text="{{REDaten\n|BAND=I,1}}\ntext\n{{REAutor|Some Author.}}", title="RE:Bla")
        factory = P577PublicationDate(re_page, None)
        claim_json = factory._get_claim_json()
        compare("+00000001893-01-01T00:00:00Z", claim_json[0]["mainsnak"]["datavalue"]["value"]["time"])

    def test__get_claim_json_R(self):
        re_page = self._create_mock_page(text="{{REDaten\n|BAND=R}}\ntext\n{{REAutor|Some Author.}}", title="RE:Bla")
        factory = P577PublicationDate(re_page, None)
        claim_json = factory._get_claim_json()
        compare("+00000001980-01-01T00:00:00Z", claim_json[0]["mainsnak"]["datavalue"]["value"]["time"])
