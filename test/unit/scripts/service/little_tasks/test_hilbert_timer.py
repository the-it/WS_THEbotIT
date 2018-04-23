from tools.catscan import PetScan
from scripts.service.little_tasks.hilbert_timer import HilbertTimer
from test import *


class TestHilbertTimer(TestCase):
    def test_get_count(self):
        with mock.patch("scripts.service.little_tasks.hilbert_timer.PetScan.run",
                        autospec=PetScan, return_value=[1,2,3]):
            self.assertEqual(3, HilbertTimer.get_count())

    def test_full_run(self):
        with mock.patch("scripts.service.little_tasks.hilbert_timer.PetScan.run",
                        autospec=PetScan) as searcher_mock:
            searcher_mock.return_value = [1,2,3]
            with mock.patch("scripts.service.little_tasks.hilbert_timer.HilbertTimer.get_days_to_end_of_2018",
                            return_value=6):
                self.assertEqual("<!--Hilbert--> Hilbert <span style=\"background:#B64900\" > 0.500</span> <!--Hilbert -->",
                                 HilbertTimer.replace_in_page("<!--Hilbert-->dummy<!--Hilbert-->"))
