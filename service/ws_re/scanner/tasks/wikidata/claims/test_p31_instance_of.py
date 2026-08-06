# pylint: disable=protected-access

from testfixtures import compare

from service.ws_re.scanner.tasks.wikidata.claims.p31_instance_of import P31InstanceOf
from service.ws_re.scanner.tasks.wikidata.claims.test_claim_factory import BaseTestClaimFactory
from tools.test import real_wiki_test


@real_wiki_test
class TestP31InstanceOf(BaseTestClaimFactory):
    def test__get_claim_json_main_aritcle(self):
        re_page = self._create_mock_page(text="{{REDaten}}\ntext\n{{REAutor|Some Author.}}", title="RE:Bla")
        factory = P31InstanceOf(re_page, None)
        claim_json = factory._get_claim_json()
        compare(13433827, claim_json[0]["mainsnak"]["datavalue"]["value"]["numeric-id"])

    def test__get_claim_json_main_cross_reference(self):
        re_page = self._create_mock_page(text="{{REDaten|VERWEIS=ON}}\ntext\n{{REAutor|Some Author.}}", title="RE:Bla")
        factory = P31InstanceOf(re_page, None)
        claim_json = factory._get_claim_json()
        compare(1302249, claim_json[0]["mainsnak"]["datavalue"]["value"]["numeric-id"])

    def test__get_claim_json_index(self):
        re_page = self._create_mock_page(
            text="{{REDaten}}\ntext\n{{REAutor|Some Author.}}", title="RE:Register (Band XI)"
        )
        factory = P31InstanceOf(re_page, None)
        claim_json = factory._get_claim_json()
        compare(873506, claim_json[0]["mainsnak"]["datavalue"]["value"]["numeric-id"])

    def test__get_claim_json_prologue(self):
        re_page = self._create_mock_page(
            text="{{REDaten}}\ntext\n{{REAutor|Some Author.}}", title="RE:Vorwort (Band I)"
        )
        factory = P31InstanceOf(re_page, None)
        claim_json = factory._get_claim_json()
        compare(920285, claim_json[0]["mainsnak"]["datavalue"]["value"]["numeric-id"])
