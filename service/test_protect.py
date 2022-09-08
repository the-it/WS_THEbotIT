from unittest import TestCase, mock


class TestProtect(TestCase):
    def setUp(self):
        self.petscan_patcher = mock.patch("service.protect.PetScan")
        self.petscan_mock = self.petscan_patcher.start()
        self.run_mock = mock.Mock()
        self.petscan_mock.return_value = mock.Mock(run=self.run_mock)
        self.addCleanup(mock.patch.stopall)

    def tearDown(self):
        mock.patch.stopall()
