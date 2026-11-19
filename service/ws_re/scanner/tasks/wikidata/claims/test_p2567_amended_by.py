# pylint: disable=protected-access
from unittest import mock

from testfixtures import compare

from service.ws_re.scanner.tasks.wikidata.claims._base import SnakParameter
from service.ws_re.scanner.tasks.wikidata.claims.p2567_amended_by import P2567AmendedBy
from service.ws_re.scanner.tasks.wikidata.claims.test_claim_factory import BaseTestClaimFactory


class TestP2567AmendedBy(BaseTestClaimFactory):
    def setUp(self) -> None:
        super().setUp()
        # don't clone the register data repository from github for every factory
        authors_patch = mock.patch("service.ws_re.scanner.tasks.wikidata.claims.claim_factory.Authors")
        authors_patch.start()
        self.addCleanup(authors_patch.stop)

    def test__get_claim_json_(self):
        # first article is the original lemma, the two following ones are amendments
        re_page = self._create_mock_page(
            text="{{REDaten|BAND=I,1}}\ntext\n{{REAutor|Hug.}}\n"
            "{{REDaten|BAND=S I}}\ntext\n{{REAutor|Hug.}}\n"
            "{{REDaten|BAND=S II}}\ntext\n{{REAutor|Hug.}}",
            title="RE:Abacus 9",
        )
        factory = P2567AmendedBy(re_page, self.logger)
        # the sub factories need live data (wikidata items, volume register), replace them by canned answers
        factory.p1433_published_in = mock.Mock()
        factory.p1433_published_in.get_volume_snak.return_value = SnakParameter(
            property_str="P1433", target_type="wikibase-item", target="Q26469512"
        )
        factory.p50_author = mock.Mock()
        factory.p50_author.get_author_list.return_value = [
            SnakParameter(property_str="P50", target_type="wikibase-item", target="Q2645561")
        ]
        factory.p577_publication_date = mock.Mock()
        factory.p577_publication_date.get_snack.return_value = SnakParameter(
            property_str="P577", target_type="time", target="1918"
        )
        factory.p3903_column = mock.Mock()
        factory.p3903_column.get_column_snak.return_value = SnakParameter(
            property_str="P3903", target_type="string", target="4–13"
        )
        factory.p155_follows = mock.Mock()
        factory.p155_follows.get_item_of_neighbour_lemma.return_value = SnakParameter(
            property_str="P155", target_type="wikibase-item", target="Q34406936"
        )
        factory.p156_followed_by = mock.Mock()
        factory.p156_followed_by.get_item_of_neighbour_lemma.return_value = SnakParameter(
            property_str="P156", target_type="wikibase-item", target="Q19980875"
        )

        claim_json = factory._get_claim_json()

        compare(2, len(claim_json))
        compare(
            {
                "mainsnak": {
                    "datatype": "wikibase-item",
                    "datavalue": {
                        "type": "wikibase-entityid",
                        "value": {"entity-type": "item", "numeric-id": 26469512},
                    },
                    "property": "P2567",
                    "snaktype": "value",
                },
                "qualifiers": {
                    "P155": [
                        {
                            "datatype": "wikibase-item",
                            "datavalue": {
                                "type": "wikibase-entityid",
                                "value": {"entity-type": "item", "numeric-id": 34406936},
                            },
                            "property": "P155",
                            "snaktype": "value",
                        }
                    ],
                    "P156": [
                        {
                            "datatype": "wikibase-item",
                            "datavalue": {
                                "type": "wikibase-entityid",
                                "value": {"entity-type": "item", "numeric-id": 19980875},
                            },
                            "property": "P156",
                            "snaktype": "value",
                        }
                    ],
                    "P3903": [
                        {
                            "datatype": "string",
                            "datavalue": {"type": "string", "value": "4–13"},
                            "property": "P3903",
                            "snaktype": "value",
                        }
                    ],
                    "P50": [
                        {
                            "datatype": "wikibase-item",
                            "datavalue": {
                                "type": "wikibase-entityid",
                                "value": {"entity-type": "item", "numeric-id": 2645561},
                            },
                            "property": "P50",
                            "snaktype": "value",
                        }
                    ],
                    "P585": [
                        {
                            "datatype": "time",
                            "datavalue": {
                                "type": "time",
                                "value": {
                                    "after": 0,
                                    "before": 0,
                                    "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                                    "precision": 9,
                                    "time": "+00000001918-01-01T00:00:00Z",
                                    "timezone": 0,
                                },
                            },
                            "property": "P585",
                            "snaktype": "value",
                        }
                    ],
                },
                "qualifiers-order": ["P50", "P585", "P3903", "P155", "P156"],
                "rank": "normal",
                "type": "statement",
            },
            claim_json[0],
        )
