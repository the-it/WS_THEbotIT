# pylint: disable=protected-access
from unittest.mock import MagicMock

from testfixtures import compare

from service.ws_re.scanner.tasks.wikidata.claims.p155_follows_p156_followed_by import (
    Neighbour,
    P155Follows,
    P156FollowedBy,
)
from service.ws_re.scanner.tasks.wikidata.claims.test_claim_factory import BaseTestClaimFactory
from tools.test import real_wiki_test


@real_wiki_test
class TestNeighbours(BaseTestClaimFactory):
    def test_neighbour_of_the_base_class_is_not_implemented(self):
        factory = Neighbour(MagicMock(), self.logger)
        with self.assertRaises(NotImplementedError):
            _ = factory.neighbour

    def test__get_claim_json_no_follows_exists(self):
        re_page = self._create_mock_page(text="{{REDaten\n|VORGÄNGER=OFF}}\ntext\n{{REAutor|Blub}}", title="RE:Bla")
        factory = P155Follows(re_page, self.logger)
        claim_json = factory._get_claim_json()
        compare(0, len(claim_json))

    def test__get_claim_json_no_follows_lemma_exists(self):
        re_page = self._create_mock_page(
            text="{{REDaten\n|VORGÄNGER=Vorwort (Band I)}}\ntext\n{{REAutor|Blub}}", title="RE:Bla"
        )
        factory = P155Follows(re_page, self.logger)
        claim_json = factory._get_claim_json()
        compare(33127714, claim_json[0]["mainsnak"]["datavalue"]["value"]["numeric-id"])

    def test__get_claim_json_no_followed_by_lemma_exists(self):
        re_page = self._create_mock_page(
            text="{{REDaten\n|NACHFOLGER=Abkürzungen}}\ntext\n{{REAutor|Blub}}", title="RE:Bla"
        )
        factory = P156FollowedBy(re_page, self.logger)
        claim_json = factory._get_claim_json()
        compare(33127715, claim_json[0]["mainsnak"]["datavalue"]["value"]["numeric-id"])
