# pylint: disable=protected-access
import pywikibot
from testfixtures import compare

from service.ws_re.scanner.tasks.wikidata.claims.p2567_amended_by import P2567AmendedBy
from service.ws_re.scanner.tasks.wikidata.claims.test_claim_factory import \
    BaseTestClaimFactory
from service.ws_re.template.re_page import RePage
from tools.test import real_wiki_test


@real_wiki_test
class TestP2567AmendedBy(BaseTestClaimFactory):
    def test__get_claim_json_(self):
        re_page = RePage(pywikibot.Page(self.wikisource_site, "RE:Abacus 9"))
        factory = P2567AmendedBy(re_page, self.logger)
        claim_json = factory._get_claim_json()
        compare(3, len(claim_json))
        compare(
            {'mainsnak':
                 {'datatype': 'wikibase-item',
                  'datavalue':
                      {'type': 'wikibase-entityid',
                       'value':
                           {'entity-type': 'item', 'numeric-id': 26469512}},
                  'property': 'P2567',
                  'snaktype': 'value'},
             'qualifiers':
                 {'P155':
                      [{'datatype': 'wikibase-item',
                        'datavalue':
                            {'type': 'wikibase-entityid', 'value': {'entity-type': 'item', 'numeric-id': 34406936}},
                        'property': 'P155',
                        'snaktype': 'value'}],
                  'P156':
                      [{'datatype': 'wikibase-item',
                        'datavalue':
                            {'type': 'wikibase-entityid', 'value': {'entity-type': 'item', 'numeric-id': 19980875}},
                        'property': 'P156',
                        'snaktype': 'value'}],
                  'P3903':
                      [{'datatype': 'string',
                        'datavalue':
                            {'type': 'string', 'value': '4–13'},
                        'property': 'P3903',
                        'snaktype': 'value'}],
                  'P50':
                      [{'datatype': 'wikibase-item',
                        'datavalue':
                            {'type': 'wikibase-entityid', 'value': {'entity-type': 'item', 'numeric-id': 2645561}},
                        'property': 'P50',
                        'snaktype': 'value'}],
                  'P577':
                      [{'datatype': 'time',
                        'datavalue':
                            {'type': 'time', 'value': {'after': 0,
                                                       'before': 0,
                                                       'calendarmodel': 'http://www.wikidata.org/entity/Q1985727',
                                                       'precision': 9,
                                                       'time': '+00000001918-01-01T00:00:00Z',
                                                       'timezone': 0}},
                        'property': 'P577',
                        'snaktype': 'value'}]},
             'qualifiers-order': ['P50', 'P577', 'P3903', 'P155', 'P156'],
             'rank': 'normal',
             'type': 'statement'},
            claim_json[0])
