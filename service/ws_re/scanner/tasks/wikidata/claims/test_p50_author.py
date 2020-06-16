# pylint: disable=protected-access
import pywikibot
from testfixtures import compare

from service.ws_re.scanner.tasks.wikidata.claims.p50_author import P50Author
from service.ws_re.scanner.tasks.wikidata.claims.test_claim_factory import \
    BaseTestClaimFactory
from tools.test import real_wiki_test


@real_wiki_test
class TestP50Author(BaseTestClaimFactory):
    def test__get_claim_json_no_author_available(self):
        re_page = self._create_mock_page(text="{{REDaten}}\ntext\n{{REAutor|Blub}}", title="RE:Bla")
        factory = P50Author(re_page, self.logger)
        claim_json = factory._get_claim_json()
        compare(0, len(claim_json))

    def test__get_claim_json_author_without_wiki_presence(self):
        re_page = self._create_mock_page(text="{{REDaten}}\ntext\n{{REAutor|Rusch}}", title="RE:Bla")
        factory = P50Author(re_page, self.logger)
        claim_json = factory._get_claim_json()
        compare(0, len(claim_json))

    def test__get_claim_json_bug_wagner(self):
        re_page = self._create_mock_page(text="{{REDaten}}\ntext\n{{REAutor|Wagner.}}", title="RE:Bla")
        factory = P50Author(re_page, self.logger)
        claim_json = factory._get_claim_json()
        # should be Richard Wagner (not the composer) (https://www.wikidata.org/wiki/Q2150844)
        compare(2150844, claim_json[0]["mainsnak"]["datavalue"]["value"]["numeric-id"])

    def test__get_claim_json_bug_Arderikka_2(self):
        re_page = self._create_mock_page(text="{{REDaten}}\ntext\n{{REAutor|Weissbach.}}", title="RE:Bla")
        factory = P50Author(re_page, self.logger)
        claim_json = factory._get_claim_json()
        # should be Franz Heinrich Weißbach (https://www.wikidata.org/wiki/Q106027)
        compare(106027, claim_json[0]["mainsnak"]["datavalue"]["value"]["numeric-id"])

    def test__get_claim_json_bug_find_author_without_ws_lemma(self):
        re_page = self._create_mock_page(text="{{REDaten}}\ntext\n{{REAutor|Stein.}}", title="RE:Bla")
        factory = P50Author(re_page, self.logger)
        claim_json = factory._get_claim_json()
        # should be Arthur Stein (Althistoriker) (https://www.wikidata.org/wiki/Q711593)
        compare(711593, claim_json[0]["mainsnak"]["datavalue"]["value"]["numeric-id"])

    def test__get_claim_json_bug_author_from_non_de_wikipedia(self):
        re_page = self._create_mock_page(text="{{REDaten}}\ntext\n{{REAutor|Holmberg}}", title="RE:Bla")
        factory = P50Author(re_page, self.logger)
        claim_json = factory._get_claim_json()
        # should be Erik J. Holmberg (https://www.wikidata.org/wiki/Q16649410)
        compare(16649410, claim_json[0]["mainsnak"]["datavalue"]["value"]["numeric-id"])

    def test__get_claim_json_bug_johannes_schmidt(self):
        re_page = self._create_mock_page(text="{{REDaten|BAND=III,1}}\ntext\n{{REAutor|J. Schmidt.}}", title="RE:Bla")
        factory = P50Author(re_page, self.logger)
        claim_json = factory._get_claim_json()
        # should be Johannes Schmidt, the epigrapher (https://www.wikidata.org/wiki/Q1296093)
        compare(1296093, claim_json[0]["mainsnak"]["datavalue"]["value"]["numeric-id"])
