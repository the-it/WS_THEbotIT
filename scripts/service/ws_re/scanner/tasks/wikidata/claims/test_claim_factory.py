from unittest import TestCase

import pywikibot
from testfixtures import compare

from scripts.service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory, \
    ChangedClaimsDict
from scripts.service.ws_re.template.re_page import RePage


class TestClaimFactory(TestCase):
    class P1234FactoryDummy(ClaimFactory):
        def get_claims_to_update(self, re_page: RePage, data_item: pywikibot.ItemPage) -> ChangedClaimsDict:
            return {"add": {self.get_property_string(): []}, "remove": []}

    def setUp(self) -> None:
        self.factory_dummy = self.P1234FactoryDummy()
        self.wikidata = None
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

