from unittest import mock

from scripts.service.ws_re.scanner.tasks.wikidata.claims.p31_instance_of import P31InstanceOf
from scripts.service.ws_re.scanner.tasks.wikidata.claims.test_claim_factory import \
    BaseTestClaimFactory


class TestP31InstanceOf(BaseTestClaimFactory):
    def setUp(self) -> None:
        self.factory = P31InstanceOf(self.wikidata)

    def test_get_claims_to_update(self):
        re_page = self._create_mock_page(text="{{REDaten}}\ntext\n{{REAutor|Some Author.}}", title="RE:Bla")
        no_claims = self._create_mock_item(claims={"P31": []})
        with mock.patch("scripts.service.ws_re.scanner.tasks.wikidata.claims.p31_instance_of.pywikibot.ItemPage") \
                as item_mock:
            item_mock.side_effect = self._create_mock_item
            print(self.factory.get_claims_to_update(re_page, no_claims))


