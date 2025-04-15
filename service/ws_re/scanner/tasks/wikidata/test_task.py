# pylint: disable=protected-access,no-self-use
from datetime import datetime
from unittest import TestCase, mock

import pywikibot
from testfixtures import compare

from service.ws_re.scanner.tasks.wikidata.claims._base import SnakParameter
from service.ws_re.scanner.tasks.wikidata.claims._typing import JsonClaimDict
from service.ws_re.scanner.tasks.wikidata.claims.claim_factory import ClaimFactory
from service.ws_re.scanner.tasks.wikidata.task import DATATask
from service.ws_re.template.re_page import RePage
from tools.bots.cloud.logger import WikiLogger
from tools.test import real_wiki_test


class TestDATATask(TestCase):
    class PseudoClaim:
        def __init__(self, pseudo_id: str):
            self.id = pseudo_id

    def test__create_add_summary(self):
        add_dict = {
            'claims': {
                'P31': [],
                'P361': [],
                'P1476': []
            },
            'labels': {},
            'descriptions': {},
            'sitelinks': []
        }
        compare("non_claims, P31, P361, P1476", DATATask._create_add_summary(add_dict))

    def test__create_add_summary_just_claims(self):
        add_dict = {
            'claims': {
                'P31': [],
                'P361': [],
                'P1476': []
            },
        }
        compare("P31, P361, P1476", DATATask._create_add_summary(add_dict))

    def test__create_add_summary_no_claims(self):
        add_dict = {
            'labels': {},
            'descriptions': {},
            'sitelinks': []
        }
        compare("non_claims", DATATask._create_add_summary(add_dict))

    def test__create_remove_summary(self):
        claims_to_remove = [self.PseudoClaim("P2"), self.PseudoClaim("P2"), self.PseudoClaim("P11")]
        compare("P2, P11", DATATask._create_remove_summary(claims_to_remove))
        compare("", DATATask._create_remove_summary([]))

    class P50AuthorFake(ClaimFactory):
        def _get_claim_json(self) -> list[JsonClaimDict]:
            return [self.create_claim_json(SnakParameter(property_str="P50",
                                                         target_type="wikibase-item",
                                                         target="Q123456789"))]

    class NonClaimsFake(mock.MagicMock):
        @property
        def dict(self) -> dict:
            non_claims = {"sitelinks": {"dewikisource": {
                "site": "dewikisource",
                "title": "something",
                "badges": "blub"
            }}}
            return non_claims

        def labels_and_sitelinks_has_changed(self, _) -> bool:
            return True

    @real_wiki_test
    def test_integration(self):
        edit_mock = mock.patch("service.ws_re.scanner.tasks.wikidata.task.pywikibot.ItemPage.editEntity",
                               new_callable=mock.MagicMock).start()
        remove_mock = mock.patch("service.ws_re.scanner.tasks.wikidata.task.pywikibot.ItemPage.removeClaims",
                                 new_callable=mock.MagicMock).start()
        mock.patch("service.ws_re.scanner.tasks.wikidata.task.NonClaims",
                   new_callable=self.NonClaimsFake).start()
        WS_WIKI = pywikibot.Site(code="de", fam="wikisource", user="THEbotIT")
        lemma = pywikibot.Page(WS_WIKI, "RE:Aal")  # existing wikidata_item
        data_task = DATATask(WS_WIKI,
                             WikiLogger(bot_name="Test", start_time=datetime(2000, 1, 1), log_to_screen=False),
                             True)
        data_task.claim_factories = (self.P50AuthorFake,)
        self.assertTrue(data_task.run(RePage(lemma)))
        edit_args = edit_mock.call_args_list
        remove_args = remove_mock.call_args_list
        edit_expect = {'claims':
            {'P50': [
                {'mainsnak':
                     {'datatype': 'wikibase-item',
                      'datavalue':
                          {'type': 'wikibase-entityid',
                           'value':
                               {'entity-type': 'item',
                                'numeric-id': 123456789
                                }
                           },
                      'property': 'P50',
                      'snaktype': 'value'
                      },
                 'rank': 'normal',
                 'type': 'statement'
                 }
            ]},
            'sitelinks':
                {'dewikisource':
                     {'badges': 'blub',
                      'site': 'dewikisource',
                      'title': 'something'
                      }
                 }
        }
        compare(edit_expect, edit_args[0].kwargs["data"])
        remove_expect = {'datatype': 'wikibase-item',
                         'datavalue':
                             {'type': 'wikibase-entityid',
                              'value':
                                  {'entity-type': 'item',
                                   'numeric-id': 1372802
                                   }
                              },
                         'property': 'P50',
                         'snaktype': 'value'
                         }
        compare(remove_expect, remove_args[0].kwargs["data"][0].toJSON()['mainsnak'])
        edit_expect = {'claims':
                           {'P1343':
                                [{'mainsnak':
                                      {'datatype': 'wikibase-item',
                                       'datavalue':
                                           {'type': 'wikibase-entityid',
                                            'value':
                                                {'entity-type': 'item',
                                                 'numeric-id': 1138524}
                                            },
                                       'property': 'P1343',
                                       'snaktype': 'value'},
                                  'qualifiers': {'P805': [{'datatype': 'wikibase-item',
                                                           'datavalue':
                                                               {'type': 'wikibase-entityid',
                                                                'value':
                                                                    {'entity-type': 'item',
                                                                     'numeric-id': 19979634
                                                                     }
                                                                },
                                                           'property': 'P805',
                                                           'snaktype': 'value'}
                                                          ]},
                                  'qualifiers-order': ['P805'],
                                  'rank': 'normal',
                                  'type': 'statement',
                                  'references':
                                      [{'snaks':
                                            {'P143':
                                                 [{'datatype': 'wikibase-item',
                                                   'datavalue': {
                                                       'type': 'wikibase-entityid',
                                                       'value': {'entity-type': 'item',
                                                                 'numeric-id': 15522295}},
                                                   'property': 'P143',
                                                   'snaktype': 'value'}]
                                             },
                                        'snaks-order': ['P143']
                                        }]
                                  }]
                            }
                       }
        # compare(edit_expect, edit_args[1].kwargs["data"])

    @real_wiki_test
    def test_integration_create_page(self):
        edit_mock = mock.patch("service.ws_re.scanner.tasks.wikidata.task.pywikibot.ItemPage.editEntity",
                               new_callable=mock.MagicMock).start()
        mock.patch("service.ws_re.scanner.tasks.wikidata.task.NonClaims",
                   new_callable=self.NonClaimsFake).start()
        WS_WIKI = pywikibot.Site(code="de", fam="wikisource", user="THEbotIT")
        lemma = pywikibot.Page(WS_WIKI, "Benutzer:THE IT/RE:Aba 1")  # existing wikidata_item
        data_task = DATATask(WS_WIKI,
                             WikiLogger(bot_name="Test", start_time=datetime(2000, 1, 1), log_to_screen=False),
                             True)
        data_task.claim_factories = (self.P50AuthorFake,)
        self.assertTrue(data_task.run(RePage(lemma)))
        edit_args = edit_mock.call_args_list
        edit_expect = {'claims':
            {'P50': [
                {'mainsnak':
                     {'datatype': 'wikibase-item',
                      'datavalue':
                          {'type': 'wikibase-entityid',
                           'value':
                               {'entity-type': 'item',
                                'numeric-id': 123456789
                                }
                           },
                      'property': 'P50',
                      'snaktype': 'value'
                      },
                 'rank': 'normal',
                 'type': 'statement'
                 }
            ]},
            'sitelinks':
                {'dewikisource':
                     {'badges': 'blub',
                      'site': 'dewikisource',
                      'title': 'something'
                      }
                 }
        }
        compare(edit_expect, edit_args[0].args[0])
