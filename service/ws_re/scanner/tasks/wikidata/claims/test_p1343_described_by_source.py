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

    def test_existing_qualifier(self):
        re_page = RePage(pywikibot.Page(self.wikisource_site, "RE:Iulius 133"))
        factory = P1343DescribedBySource(re_page, self.logger)
        target_item = pywikibot.ItemPage(re_page.page.data_repository, "Q1409")
        compare([34622751, 34395255], factory.get_existing_qualifiers(target_item))
        target_item = pywikibot.ItemPage(re_page.page.data_repository, "Q12345")
        compare([], factory.get_existing_qualifiers(target_item))

    def test_check_source_has_target(self):
        re_page = RePage(pywikibot.Page(self.wikisource_site, "RE:Iulius 133"))
        factory = P1343DescribedBySource(re_page, self.logger)
        # source: RE:Caligula has Caligula as main topic
        compare(True, factory.check_source_has_target(34622751, 1409))
        # source: RE:Auloneus hasn't Caligula as main topic
        compare(False, factory.check_source_has_target(19992463, 1409))
        # source: RE:Caliendrum has no main topic
        compare(False, factory.check_source_has_target(19756677, 1409))

    def test_get_qualifiers(self):
        re_page = RePage(pywikibot.Page(self.wikisource_site, "RE:Caliendrum"))
        factory = P1343DescribedBySource(re_page, self.logger)
        # get existing qualifiers and add new one
        qualifiers = factory.get_qualifiers(19756677, 1409)
        # first two already exists ... third one is added
        compare("Q34622751", qualifiers[0].target)
        compare("Q34395255", qualifiers[1].target)
        compare("Q19756677", qualifiers[2].target)

    def test_filter_claimlists(self):
        re_page = RePage(pywikibot.Page(self.wikisource_site, "RE:Caliendrum"))
        factory = P1343DescribedBySource(re_page, self.logger)

        a = pywikibot.Claim.fromJSON(self.wikidata_site, self._create_mock_json("a", "P1343"))
        b = pywikibot.Claim.fromJSON(self.wikidata_site, self._create_mock_json("b", "P1343"))
        c = pywikibot.Claim.fromJSON(self.wikidata_site, self._create_mock_json("c", "P1234"))

        new_claims = [a]
        old_claims = [b, c]

        filtered_new_claims, filtered_old_claims = factory.filter_new_vs_old_claim_list(new_claims, old_claims)
        # first two already exists ... third one is added
        compare([a], filtered_new_claims)
        compare([b], filtered_old_claims)
