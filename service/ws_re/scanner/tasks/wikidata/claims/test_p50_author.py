# pylint: disable=protected-access
import pywikibot
from testfixtures import compare

from service.ws_re.scanner.tasks.wikidata.claims.p50_author import P50Author
from service.ws_re.scanner.tasks.wikidata.claims.test_claim_factory import \
    BaseTestClaimFactory
from service.ws_re.template.re_page import RePage
from tools.test import wikidata_test, real_wiki_test


@real_wiki_test
class TestP50Author(BaseTestClaimFactory):
    @wikidata_test
    def test__get_claim_json(self):
        re_page = RePage(pywikibot.Page(self.wikisource_site, "RE:Aal"))
        factory = P50Author(re_page, self.logger)
        claim_json = factory._get_claim_json()
        # should be Eugen Oder (https://www.wikidata.org/wiki/Q1372802)
        compare(1372802, claim_json[0]["mainsnak"]["datavalue"]["value"]["numeric-id"])

    @wikidata_test
    def test__get_claim_json_bug_wagner(self):
        re_page = RePage(pywikibot.Page(self.wikisource_site, "RE:Dymas 1"))
        factory = P50Author(re_page, self.logger)
        claim_json = factory._get_claim_json()
        # should be Richard Wagner (not the composer) (https://www.wikidata.org/wiki/Q2150844)
        compare(2150844, claim_json[0]["mainsnak"]["datavalue"]["value"]["numeric-id"])
