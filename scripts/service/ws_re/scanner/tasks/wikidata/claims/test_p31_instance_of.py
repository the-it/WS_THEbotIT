from unittest import mock

from pywikibot import ItemPage

from scripts.service.ws_re.scanner.tasks.wikidata.claims.p31_instance_of import P31InstanceOf
from scripts.service.ws_re.scanner.tasks.wikidata.claims.test_claim_factory import \
    BaseTestClaimFactory


class TestP31InstanceOf(BaseTestClaimFactory):
    def setUp(self) -> None:
        site_mock = mock.MagicMock()
        self.factory = P31InstanceOf(site_mock)
        # mock all calls to ItemPage, to not really create Items at Wikidata
        self.item_mock = mock.patch(
            "scripts.service.ws_re.scanner.tasks.wikidata.claims.p31_instance_of.pywikibot.ItemPage").start()
        self.item_mock.side_effect = self._create_mock_item
        # sadly I have to mock some pywikibot internals to be able to call Claim.setTarget()
        self.types_mock = mock.patch(
            "scripts.service.ws_re.scanner.tasks.wikidata.claims.p31_instance_of.pywikibot.Claim.types").start()
        self.types_mock.__getitem__.return_value = mock.MagicMock

    def tearDown(self) -> None:
        mock.patch.stopall()

    def test_get_claims_to_update(self):
        re_page = self._create_mock_page(text="{{REDaten}}\ntext\n{{REAutor|Some Author.}}", title="RE:Bla")
        no_claims = self._create_mock_item(claims={"P31": []})
        print(self.factory.get_claims_to_update(re_page, no_claims))


