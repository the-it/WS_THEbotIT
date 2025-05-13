# pylint: disable=protected-access
import pywikibot
from testfixtures import compare

from service.ws_re.scanner.tasks.wikidata.claims.p13269_directs_readers_to import P13269DirectsReadersTo
from service.ws_re.scanner.tasks.wikidata.claims.test_claim_factory import \
    BaseTestClaimFactory
from service.ws_re.template.re_page import RePage
from tools.test import real_wiki_test


class TestP13269DirectsReadersTo(BaseTestClaimFactory):
    def test__get_claim_json_no_redirect(self):
        re_page = self._create_mock_page(text="{{REDaten}}\ntext\n{{REAutor|Some Author.}}", title="RE:Bla")
        factory = P13269DirectsReadersTo(re_page, self.logger)
        claim_json = factory._get_claim_json()
        compare([], claim_json)

    @real_wiki_test
    def test__get_claim_json(self):
        re_page = RePage(pywikibot.Page(self.wikisource_site, "RE:Amantes 2"))
        factory = P13269DirectsReadersTo(re_page, self.logger)
        claim_json = factory._get_claim_json()
        expected_claim_json = [{'mainsnak':
                                    {'snaktype': 'value',
                                     'property': 'P13269',
                                     'datatype': 'wikibase-item',
                                     'datavalue':
                                         {'value':
                                              {'entity-type': 'item',
                                               'numeric-id': 19985952
                                               },
                                          'type': 'wikibase-entityid'
                                          }
                                     },
                                'type': 'statement',
                                'rank': 'normal'
                                }]
        compare(expected_claim_json, claim_json)
