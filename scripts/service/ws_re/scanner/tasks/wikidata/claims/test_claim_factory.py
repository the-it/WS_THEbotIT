from typing import Dict, List
from unittest import TestCase
from unittest.mock import MagicMock, PropertyMock, Mock

import pywikibot
from testfixtures import compare

from scripts.service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory, \
    ChangedClaimsDict
from scripts.service.ws_re.template.re_page import RePage


class BaseTestClaimFactory(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wikidata = None

    def _create_mock_item(self,
                          site: pywikibot.Site = None,
                          title: str = "Q1",
                          claims: Dict[str, List[pywikibot.Claim]] = None):
        mock_item = MagicMock()
        if claims:
            claims_mock = PropertyMock(return_value=claims)
            type(mock_item).claims = claims_mock
        return mock_item

    def _create_mock_page(self, text: str = None, title: str = None):
        mock_item = MagicMock()
        if text:
            text_mock = PropertyMock(return_value=text)
            type(mock_item).text = text_mock
        if title:
            title_mock = Mock(return_value=title)
            type(mock_item).title = title
        return RePage(mock_item)


class TestClaimFactory(BaseTestClaimFactory):
    class P1234FactoryDummy(ClaimFactory):
        def get_claims_to_update(self, re_page: RePage, data_item: pywikibot.ItemPage) -> ChangedClaimsDict:
            return {"add": {self.get_property_string(): []}, "remove": []}

    def setUp(self) -> None:
        self.factory_dummy = self.P1234FactoryDummy(self.wikidata)
        self.base_json = {'mainsnak': {'snaktype': 'value',
                                       'property': 'P1234',
                                       'datatype': 'string',
                                       'datavalue': {'value': 'a', 'type': 'string'}},
                          'type': 'statement',
                          'rank': 'normal'}
        self.a = pywikibot.Claim.fromJSON(self.wikidata, self.base_json)
        self.base_json["mainsnak"]["datavalue"]["value"] = "b"
        self.b = pywikibot.Claim.fromJSON(self.wikidata, self.base_json)
        self.base_json["mainsnak"]["datavalue"]["value"] = "c"
        self.c = pywikibot.Claim.fromJSON(self.wikidata, self.base_json)
        self.base_json["mainsnak"]["datavalue"]["value"] = "d"
        self.d = pywikibot.Claim.fromJSON(self.wikidata, self.base_json)

    def test_property_string(self):
        compare("P1234", self.P1234FactoryDummy.get_property_string())

    def test__filter_new_vs_old_claim_list(self):
        compare(([self.a, self.c], [self.d]),
                self.factory_dummy._filter_new_vs_old_claim_list([self.a, self.b, self.c], [self.b, self.d]))
        compare(([self.a], []), self.factory_dummy._filter_new_vs_old_claim_list([self.a], []))
        compare(([], [self.a]), self.factory_dummy._filter_new_vs_old_claim_list([], [self.a]))
        compare(([], []),
                self.factory_dummy._filter_new_vs_old_claim_list([self.a, self.b, self.c], [self.a, self.b, self.c]))

    def test__create_claim_dictionary(self):
        compare({"add": {"P1234": [self.a, self.b]}, "remove": [self.c, self.d]},
                self.factory_dummy._create_claim_dictionary([self.a, self.b], [self.c, self.d]))
