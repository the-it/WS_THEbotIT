from testfixtures import compare

from service.ws_re.scanner.tasks.wikidata.claims.p3903_column import P3903Column
from service.ws_re.scanner.tasks.wikidata.claims.test_claim_factory import \
    BaseTestClaimFactory


class TestP3903Column(BaseTestClaimFactory):
    def test__get_claim_json_start_and_end(self):
        re_page = self._create_mock_page(
            text="{{REDaten|SPALTE_START=1|SPALTE_END=2}}\ntext\n{{REAutor|Some Author.}}", title="RE:Bla")
        factory = P3903Column(re_page)
        claim_json = factory._get_claim_json()
        compare("1–2", claim_json[0]["mainsnak"]["datavalue"]["value"])

    def test__get_claim_json_only_start(self):
        re_page = self._create_mock_page(text="{{REDaten|SPALTE_START=12}}\ntext\n{{REAutor|Some Author.}}",
                                         title="RE:Bla")
        factory = P3903Column(re_page)
        claim_json = factory._get_claim_json()
        compare("12", claim_json[0]["mainsnak"]["datavalue"]["value"])

        re_page = self._create_mock_page(
            text="{{REDaten|SPALTE_START=123|SPALTE_END=}}\ntext\n{{REAutor|Some Author.}}", title="RE:Bla")
        factory = P3903Column(re_page)
        claim_json = factory._get_claim_json()
        compare("123", claim_json[0]["mainsnak"]["datavalue"]["value"])

        re_page = self._create_mock_page(
            text="{{REDaten|SPALTE_START=1234|SPALTE_END=OFF}}\ntext\n{{REAutor|Some Author.}}", title="RE:Bla")
        factory = P3903Column(re_page)
        claim_json = factory._get_claim_json()
        compare("1234", claim_json[0]["mainsnak"]["datavalue"]["value"])
