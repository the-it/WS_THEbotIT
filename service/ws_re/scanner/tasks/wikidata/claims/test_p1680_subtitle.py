# pylint: disable=protected-access

from testfixtures import compare

from service.ws_re.scanner.tasks.wikidata.claims.p1680_subtitle import P1680Subtitle
from service.ws_re.scanner.tasks.wikidata.claims.test_claim_factory import \
    BaseTestClaimFactory


class TestP1680Subtitle(BaseTestClaimFactory):
    def test__get_claim_json_main_aritcle(self):
        re_page = self._create_mock_page(text="""{{REDaten}}
'''Bizone''' ({{Polytonisch|Βιζώνη}}), ein Städtchen am thrak...
{{REAutor|Some Author.}}""",
                                         title="RE:Bizone")
        factory = P1680Subtitle(re_page)
        claim_json = factory._get_claim_json()
        compare("Βιζώνη", claim_json[0]["mainsnak"]["datavalue"]["value"]["text"])

    def test__get_claim_json_main_aritcle_no_markup(self):
        re_page = self._create_mock_page(text="""{{REDaten}}
'''Bizone''' (Βιζώνη), ein Städtchen am thrak...
{{REAutor|Some Author.}}""",
                                         title="RE:Bizone")
        factory = P1680Subtitle(re_page)
        claim_json = factory._get_claim_json()
        compare("Βιζώνη", claim_json[0]["mainsnak"]["datavalue"]["value"]["text"])

    def test__get_claim_json_main_aritcle_no_subtitle(self):
        re_page = self._create_mock_page(text="""{{REDaten}}
'''Bizone''', ein Städtchen am thrak...
{{REAutor|Some Author.}}""",
                                         title="RE:Bizone")
        factory = P1680Subtitle(re_page)
        compare([], factory._get_claim_json())
