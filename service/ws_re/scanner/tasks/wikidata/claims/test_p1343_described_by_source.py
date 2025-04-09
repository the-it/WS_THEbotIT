# pylint: disable=protected-access
import pywikibot
from testfixtures import compare

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
