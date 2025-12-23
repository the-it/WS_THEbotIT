# pylint: disable=protected-access
import pywikibot
from testfixtures import compare

from service.ws_re.scanner.tasks.wikidata.claims._base import SnakParameter
from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory
from service.ws_re.scanner.tasks.wikidata.claims.p1343_described_by_source import P1343DescribedBySource
from service.ws_re.scanner.tasks.wikidata.claims.test_claim_factory import BaseTestClaimFactory
from service.ws_re.template.re_page import RePage
from tools.test import real_wiki_test


@real_wiki_test
class TestP1343DescribedBySource(BaseTestClaimFactory):
    def test__get_claim_json(self):
        re_page = RePage(pywikibot.Page(self.wikisource_site, "RE:Aal"))
        factory = P1343DescribedBySource(re_page, self.logger)
        claim_json = factory._get_claim_json()
        compare(19979634, claim_json[0]["qualifiers"]["P805"][0]["datavalue"]["value"]["numeric-id"])

    def test__get_claim_json_nothing_to_see(self):
        re_page = RePage(pywikibot.Page(self.wikisource_site, "RE:Ameirake"))
        factory = P1343DescribedBySource(re_page, self.logger)
        claim_json = factory._get_claim_json()
        compare([], claim_json)

    def test_existing_qualifier(self):
        re_page = RePage(pywikibot.Page(self.wikisource_site, "RE:Confluentes 1"))
        factory = P1343DescribedBySource(re_page, self.logger)
        # Wikidata item Confluentes, has two proper RE arcticle items
        target_item = pywikibot.ItemPage(re_page.page.data_repository, "Q1125398")
        compare([19994718, 19994710], factory.get_existing_qualifiers(target_item))
        target_item = pywikibot.ItemPage(re_page.page.data_repository, "Q12345")
        compare([], factory.get_existing_qualifiers(target_item))

    def test_empty_qualifier(self):
        # Colonia 1 has a central topic, but is a cross-reference ... so no claim should be created
        re_page = RePage(pywikibot.Page(self.wikisource_site, "RE:Colonia 1"))
        factory = P1343DescribedBySource(re_page, self.logger)
        claim_json = factory._get_claim_json()
        # resulting claim has only one qualifier, which isn't the data item of RE:Colonia 1 (34621354)
        compare(1, len(claim_json[0]["qualifiers"]))
        # instead it is RE:Coloniae
        compare(51885370, claim_json[0]["qualifiers"]["P805"][0]["datavalue"]["value"]["numeric-id"])

    def test_check_source_has_target(self):
        re_page = RePage(pywikibot.Page(self.wikisource_site, "RE:Iulius 133"))
        factory = P1343DescribedBySource(re_page, self.logger)
        # source: RE:Caligula has Caligula as main topic, but is a cross-reference
        compare(False, factory.check_source_is_valid(34622751, 1409))
        # source: RE:Iulius 133 has Caligula as main topic, is a main article
        compare(True, factory.check_source_is_valid(34395255, 1409))
        # source: RE:Auloneus hasn't Caligula as main topic
        compare(False, factory.check_source_is_valid(19992463, 1409))
        # source: RE:Caliendrum has no main topic
        compare(False, factory.check_source_is_valid(19756677, 1409))

    def test_filter_claimlists(self):
        re_page = RePage(pywikibot.Page(self.wikisource_site, "RE:Caliendrum"))
        factory = P1343DescribedBySource(re_page, self.logger)

        qualifier_a = SnakParameter(property_str="P805",
                                    target_type="wikibase-item",
                                    target="Q123")
        qualifier_b = SnakParameter(property_str="P805",
                                    target_type="wikibase-item",
                                    target="Q1234")
        qualifier_c = SnakParameter(property_str="P805",
                                    target_type="wikibase-item",
                                    target="Q12345")
        main_snak_re = SnakParameter(property_str="P1343",
                                     target_type="wikibase-item",
                                     target="Q1138524")
        main_snak_else = SnakParameter(property_str="P1343",
                                       target_type="wikibase-item",
                                       target="Q123456")

        a = pywikibot.Claim.fromJSON(self.wikidata_site,
                                     ClaimFactory.create_claim_json(main_snak_re, qualifiers=[qualifier_a]))
        b = pywikibot.Claim.fromJSON(self.wikidata_site,
                                     ClaimFactory.create_claim_json(main_snak_re, qualifiers=[qualifier_b]))
        c = pywikibot.Claim.fromJSON(self.wikidata_site,
                                     ClaimFactory.create_claim_json(main_snak_else, qualifiers=[qualifier_c]))

        new_claims = [a]
        old_claims = [b, c]

        filtered_new_claims, filtered_old_claims = factory.filter_new_vs_old_claim_list(new_claims, old_claims)
        # first two already exists ... third one is added
        compare([a], filtered_new_claims)
        compare([b], filtered_old_claims)

    def test_integration(self):
        re_page = RePage(pywikibot.Page(self.wikisource_site, "RE:Δικτυοβόλος"))
        factory = P1343DescribedBySource(re_page, self.logger)
        claims = factory._get_claim_json()
        expect = [{'mainsnak':
                       {'datatype': 'wikibase-item',
                        'datavalue':
                            {'type': 'wikibase-entityid',
                             'value':
                                 {'entity-type': 'item',
                                  'numeric-id': 1138524
                                  }
                             },
                        'property': 'P1343',
                        'snaktype': 'value'
                        },
                   'qualifiers':
                       {'P805':
                           [
                               {'datatype': 'wikibase-item',
                                'datavalue':
                                    {'type': 'wikibase-entityid',
                                     'value': {'entity-type': 'item', 'numeric-id': 19995086}
                                     },
                                'property': 'P805',
                                'snaktype': 'value'
                                }
                           ]
                       },
                   'qualifiers-order': ['P805'],
                   'rank': 'normal',
                   'references':
                       [{'snaks': {'P143': [{'datatype': 'wikibase-item',
                                             'datavalue': {'type': 'wikibase-entityid',
                                                           'value': {'entity-type': 'item',
                                                                     'numeric-id': 15522295}},
                                             'property': 'P143',
                                             'snaktype': 'value'}]},
                         'snaks-order': ['P143']}],
                   'type': 'statement'
                   }
                  ]
        compare(claims, expect)
