# pylint: disable=protected-access,no-self-use
from datetime import datetime
from typing import List, Optional
from unittest import TestCase
from unittest.mock import MagicMock, PropertyMock, Mock

import pywikibot
from testfixtures import compare

from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory
from service.ws_re.scanner.tasks.wikidata.claims._base import SnakParameter
from service.ws_re.scanner.tasks.wikidata.claims._typing import JsonClaimDict
from service.ws_re.template.re_page import RePage
from tools.bots import BotException
from tools.bots.pi import WikiLogger
from tools.test import REAL_WIKI_TEST


class BaseTestClaimFactory(TestCase):
    def setUp(self) -> None:
        if REAL_WIKI_TEST:
            self.wikisource_site = pywikibot.Site(code='de', fam='wikisource', user='THEbotIT')
            self.wikidata_site = self.wikisource_site.data_repository()
        else:
            self.wikidata_site = MagicMock()
            self.wikisource_site = MagicMock()
        self.logger = WikiLogger(bot_name="Test",
                                 start_time=datetime(2000, 1, 1),
                                 log_to_screen=False)

    @staticmethod
    def _create_mock_page(text: Optional[str] = None, title: Optional[str] = None):
        mock_item = MagicMock()
        if text:
            text_mock = PropertyMock(return_value=text)
            type(mock_item).text = text_mock
        if title:
            title_mock = Mock(return_value=title)
            type(mock_item).title = title_mock
        return RePage(mock_item)


class TestClaimFactory(BaseTestClaimFactory):
    class P1234FactoryDummy(ClaimFactory):
        def _get_claim_json(self) -> List[JsonClaimDict]:
            return []

    def setUp(self) -> None:
        super().setUp()
        self.factory_dummy = self.P1234FactoryDummy(MagicMock(), self.logger)

        def get_json(letter: str):
            return {"mainsnak": {"snaktype": "value",
                                 "property": "P1234",
                                 "datatype": "string",
                                 "datavalue": {"value": letter, "type": "string"}},
                    "type": "statement",
                    "rank": "normal"}

        self.a = pywikibot.Claim.fromJSON(self.wikidata_site, get_json("a"))
        self.b = pywikibot.Claim.fromJSON(self.wikidata_site, get_json("b"))
        self.c = pywikibot.Claim.fromJSON(self.wikidata_site, get_json("c"))
        self.d = pywikibot.Claim.fromJSON(self.wikidata_site, get_json("d"))

    def test_property_string(self):
        compare("P1234", self.P1234FactoryDummy.get_property_string())

    def test__filter_new_vs_old_claim_list(self):
        compare(([self.a, self.c], [self.d]),
                self.factory_dummy.filter_new_vs_old_claim_list([self.a, self.b, self.c], [self.b, self.d]))
        compare(([self.a], []), self.factory_dummy.filter_new_vs_old_claim_list([self.a], []))
        compare(([], [self.a]), self.factory_dummy.filter_new_vs_old_claim_list([], [self.a]))
        compare(([], []),
                self.factory_dummy.filter_new_vs_old_claim_list([self.a, self.b, self.c], [self.a, self.b, self.c]))

    def test__create_claim_dictionary(self):
        compare({"add": {"P1234": [self.a, self.b]}, "remove": [self.c, self.d]},
                self.factory_dummy._create_claim_dictionary([self.a, self.b], [self.c, self.d]))

    def test__create_claim_json_wikibase_item(self):
        expect = {"mainsnak": {"snaktype": "value",
                               "property": "P31",
                               "datatype": "wikibase-item",
                               "datavalue": {
                                   "value": {
                                       "entity-type": "item",
                                       "numeric-id": 123
                                   },
                                   "type": "wikibase-entityid"
                               }},
                  "type": "statement",
                  "rank": "normal"}

        compare(expect, ClaimFactory.create_claim_json(
            SnakParameter(property_str="P31", target_type="wikibase-item", target="Q123")))
        compare(expect, ClaimFactory.create_claim_json(
            SnakParameter(property_str="P31", target_type="wikibase-item", target="123")))

    def test__create_claim_json_time_just_year(self):
        expect = {"mainsnak": {"snaktype": "value",
                               "property": "P31",
                               "datatype": "time",
                               "datavalue": {
                                   "value": {
                                       "time": "+00000001234-01-01T00:00:00Z",
                                       "precision": 9,
                                       "after": 0,
                                       "before": 0,
                                       "timezone": 0,
                                       "calendarmodel": "http://www.wikidata.org/entity/Q1985727"
                                   },
                                   "type": "time"}},
                  "type": "statement",
                  "rank": "normal"}

        compare(expect, ClaimFactory.create_claim_json(
            SnakParameter(property_str="P31", target_type="time", target="1234")))

    def test__create_claim_json_string(self):
        expect = {"mainsnak": {"snaktype": "value",
                               "property": "P31",
                               "datatype": "string",
                               "datavalue": {"value": "texttexttext",
                                             "type": "string"
                                             }},
                  "type": "statement",
                  "rank": "normal"}

        compare(expect, ClaimFactory.create_claim_json(
            SnakParameter(property_str="P31", target_type="string", target="texttexttext")))

    def test__create_claim_json_monolingualtext(self):
        expect = {"mainsnak": {"snaktype": "value",
                               "property": "P31",
                               "datatype": "monolingualtext",
                               "datavalue": {"value": {"text": "texttexttext",
                                                       "language": "mul"},
                                             "type": "monolingualtext"
                                             }
                               },
                  "type": "statement",
                  "rank": "normal"}

        compare(expect, ClaimFactory.create_claim_json(
            SnakParameter(property_str="P31", target_type="monolingualtext", target="texttexttext")))

    def test__create_claim_json_with_qualifier(self):
        expect = {"mainsnak": {"snaktype": "value",
                               "property": "P31",
                               "datatype": "string",
                               "datavalue": {"value": "texttexttext",
                                             "type": "string"
                                             }},
                  "type": "statement",
                  "rank": "normal",
                  "qualifiers": {
                      "P1234": [
                          {
                              "snaktype": "value",
                              "property": "P1234",
                              "datatype": "string",
                              "datavalue": {
                                  "value": "text",
                                  "type": "string"
                              }
                          }
                      ],
                      "P5678": [
                          {
                              "snaktype": "value",
                              "property": "P5678",
                              "datatype": "wikibase-item",
                              "datavalue": {
                                  "value": {
                                      "entity-type": "item",
                                      "numeric-id": 123456
                                  },
                                  "type": "wikibase-entityid"
                              }
                          }
                      ]
                  },
                  "qualifiers-order": [
                      "P1234",
                      "P5678"
                  ]
                  }

        main_parameter = SnakParameter(property_str="P31", target_type="string", target="texttexttext")
        quali_snak_1 = SnakParameter(property_str="P1234", target_type="string", target="text")
        quali_snak_2 = SnakParameter(property_str="P5678", target_type="wikibase-item", target="Q123456")
        compare(expect, ClaimFactory.create_claim_json(main_parameter, qualifiers=[quali_snak_1, quali_snak_2]))

    def test__create_claim_json_with_reference(self):
        expect = {
            "mainsnak": {
                "snaktype": "value",
                "property": "P1234",
                "datatype": "string",
                "datavalue": {
                    "value": "value",
                    "type": "string"
                }
            },
            "type": "statement",
            "rank": "normal",
            "references": [
                {
                    "snaks": {
                        "P123": [
                            {
                                "snaktype": "value",
                                "property": "P123",
                                "datatype": "string",
                                "datavalue": {
                                    "value": "ref1",
                                    "type": "string"
                                }
                            }
                        ],
                        "P234": [
                            {
                                "snaktype": "value",
                                "property": "P234",
                                "datatype": "string",
                                "datavalue": {
                                    "value": "ref2",
                                    "type": "string"
                                }
                            }
                        ]
                    },
                    "snaks-order": [
                        "P123",
                        "P234"
                    ]
                },
                {
                    "snaks": {
                        "P345": [
                            {
                                "snaktype": "value",
                                "property": "P345",
                                "datatype": "string",
                                "datavalue": {
                                    "value": "ref3",
                                    "type": "string"
                                }
                            }
                        ],
                        "P456": [
                            {
                                "snaktype": "value",
                                "property": "P456",
                                "datatype": "string",
                                "datavalue": {
                                    "value": "ref4",
                                    "type": "string"
                                }
                            }
                        ]
                    },
                    "snaks-order": [
                        "P345",
                        "P456"
                    ]
                }
            ]
        }

        main_parameter = SnakParameter(property_str="P1234", target_type="string", target="value")
        ref_snak_1 = SnakParameter(property_str="P123", target_type="string", target="ref1")
        ref_snak_2 = SnakParameter(property_str="P234", target_type="string", target="ref2")
        ref_snak_3 = SnakParameter(property_str="P345", target_type="string", target="ref3")
        ref_snak_4 = SnakParameter(property_str="P456", target_type="string", target="ref4")
        compare(expect, ClaimFactory.create_claim_json(snak_parameter=main_parameter,
                                                       references=[[ref_snak_1, ref_snak_2],
                                                                   [ref_snak_3, ref_snak_4]]))

    def test__create_claim_json_exception(self):
        with self.assertRaises(BotException):
            ClaimFactory.create_claim_json(SnakParameter(property_str="P31", target_type="tada", target="123"))
        with self.assertRaises(ValueError):
            ClaimFactory.create_claim_json(SnakParameter(property_str="P31", target_type="time", target="tada"))
