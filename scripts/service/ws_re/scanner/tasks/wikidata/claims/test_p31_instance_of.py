from unittest import mock

import pywikibot
from pywikibot import ItemPage
from testfixtures import compare

from scripts.service.ws_re.scanner.tasks.wikidata.claims.p31_instance_of import P31InstanceOf
from scripts.service.ws_re.scanner.tasks.wikidata.claims.test_claim_factory import \
    BaseTestClaimFactory


class TestP31InstanceOf(BaseTestClaimFactory):
    def setUp(self) -> None:
        site_mock = mock.MagicMock()
        self.factory = P31InstanceOf(site_mock)

    def test_get_claims_to_update_different_claim(self):
        re_page = self._create_mock_page(text="{{REDaten}}\ntext\n{{REAutor|Some Author.}}", title="RE:Bla")
        claim_dict = {'mainsnak': {'snaktype': 'value',
                                   'property': "P31",
                                   "datatype": "wikibase-item",
                                   "datavalue": {
                                       "value": {
                                           "entity-type": "item",
                                           "numeric-id": 1234
                                       },
                                       "type": "wikibase-entityid"
                                   }},
                      'type': 'statement',
                      'rank': 'normal'}
        claim = pywikibot.Claim.fromJSON(self.wikidata, claim_dict)
        diffenrent_claims = self._create_mock_item(claims={"P31": [claim]})
        claim_dict = self.factory.get_claims_to_update(re_page, diffenrent_claims)
        compare("Q13433827", str(claim_dict["add"]["P31"][0].target))
        compare("Q1234", str(claim_dict["remove"][0].target))

    def test_get_claims_to_update_identic_claim(self):
        re_page = self._create_mock_page(text="{{REDaten}}\ntext\n{{REAutor|Some Author.}}", title="RE:Bla")
        claim_dict = {'mainsnak': {'snaktype': 'value',
                                   'property': "P31",
                                   "datatype": "wikibase-item",
                                   "datavalue": {
                                       "value": {
                                           "entity-type": "item",
                                           "numeric-id": 13433827
                                       },
                                       "type": "wikibase-entityid"
                                   }},
                      'type': 'statement',
                      'rank': 'normal'}
        claim = pywikibot.Claim.fromJSON(self.wikidata, claim_dict)
        diffenrent_claims = self._create_mock_item(claims={"P31": [claim]})
        claim_dict = self.factory.get_claims_to_update(re_page, diffenrent_claims)
        compare({}, claim_dict["add"])
        compare([], claim_dict["remove"])
