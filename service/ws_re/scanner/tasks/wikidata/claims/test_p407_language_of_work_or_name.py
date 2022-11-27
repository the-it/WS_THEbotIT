# pylint: disable=protected-access

from testfixtures import compare

from service.ws_re.scanner.tasks.wikidata.claims.p407_language_of_work_or_name import P407LanguageOfWorkOrName
from service.ws_re.scanner.tasks.wikidata.claims.test_claim_factory import \
    BaseTestClaimFactory


class TestP407LanguageOfWorkOrName(BaseTestClaimFactory):
    def test__get_claim_json(self):
        re_page = self._create_mock_page(text="{{REDaten}}\ntext\n{{REAutor|Some Author.}}", title="RE:Bla")
        factory = P407LanguageOfWorkOrName(re_page, None)
        claim_json = factory._get_claim_json()
        compare(188, claim_json[0]["mainsnak"]["datavalue"]["value"]["numeric-id"])
