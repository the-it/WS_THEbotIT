# pylint: disable=protected-access
import pywikibot
from testfixtures import compare

from service.ws_re.scanner.tasks.wikidata.claims.p6216_copyright_status import P6216CopyrightStatus
from service.ws_re.scanner.tasks.wikidata.claims.test_claim_factory import \
    BaseTestClaimFactory
from service.ws_re.template.re_page import RePage
from tools.test import wikidata_test, real_wiki_test


@real_wiki_test
class TestP6216CopyrightStatus(BaseTestClaimFactory):
    #@wikidata_test
    def test__get_claim_json(self):
        re_page = RePage(pywikibot.Page(self.wikisource_site, "RE:Atreus"))
        factory = P6216CopyrightStatus(re_page, self.logger)
        claim_json = factory._get_claim_json()
        compare(1372802, claim_json[0]["mainsnak"]["datavalue"]["value"]["numeric-id"])
