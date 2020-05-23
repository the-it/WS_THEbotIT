# pylint: disable=protected-access

from testfixtures import compare

from service.ws_re.scanner.tasks.wikidata.claims.p31_instance_of import P31InstanceOf
from service.ws_re.scanner.tasks.wikidata.claims.test_claim_factory import \
    BaseTestClaimFactory


class TestP50Author(BaseTestClaimFactory):
    def test__get_claim_json_main_aritcle(self):
        re_page =
        factory = P31InstanceOf(re_page, None)
        claim_json = factory._get_claim_json()
        compare(13433827, claim_json[0]["mainsnak"]["datavalue"]["value"]["numeric-id"])
