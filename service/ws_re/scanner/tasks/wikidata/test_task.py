# pylint: disable=protected-access,no-self-use
from unittest import TestCase

from testfixtures import compare

from service.ws_re.scanner.tasks.wikidata.task import DATATask


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

    def test__create_remove_summary(self):
        claims_to_remove = [self.PseudoClaim("P2"), self.PseudoClaim("P2"), self.PseudoClaim("P11")]
        compare("P2, P11", DATATask._create_remove_summary(claims_to_remove))
        compare("", DATATask._create_remove_summary([]))
