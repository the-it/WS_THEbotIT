# pylint: disable=no-self-use,protected-access
from datetime import datetime
from unittest import mock

from testfixtures import compare

from service.gl.status import GlStatus
from tools.bots.test_base import TestCloudBase


class TestGlStatus(TestCloudBase):
    def setUp(self):
        self.searcher_mock = mock.MagicMock()
        self.petscan_mock = mock.patch("service.gl.status.PetScan").start()
        self.petscan_mock.return_value = self.searcher_mock
        self.page_mock = mock.patch("service.gl.status.Page", new_callable=mock.MagicMock).start()
        self.addCleanup(mock.patch.stopall)

    def tearDown(self):
        mock.patch.stopall()
        super().tearDown()

    def test_projektstand(self):
        given_file = """aaa
<!--new line: Liste wird von einem Bot aktuell gehalten.-->
bbb"""
        result = """aaa
<!--new line: Liste wird von einem Bot aktuell gehalten.-->
|-
|01.01.2000|| 50000 || 25000 (50,00 %) || 15000 (30,00 %) || 10000 (20,00 %) || 9250/18500 (50,00 %) ||
bbb"""
        bot = GlStatus(None, False)
        bot.status.current_run.start_time = datetime(year=2000, month=1, day=1)
        compare(
            result,
            bot.projektstand(
                temp_text=given_file, alle=50000, fertig=10000, korrigiert=15000, unkorrigiert=25000, articles=9250
            ),
        )

    def test_to_percent(self):
        test_array = (
            ((0, 1), " (0,00 %)"),
            ((1, 4), " (25,00 %)"),
            ((1, 3), " (33,33 %)"),
            ((2, 3), " (66,67 %)"),
            ((3, 3), " (100,00 %)"),
        )

        bot = GlStatus(None, False)
        for pair in test_array:
            compare(pair[1], bot.to_percent(*pair[0]))

    def test_alle_seiten(self):
        given = "aaa<!--GLStatus:alle_Seiten-->12345<!---->bbb"
        compare("aaa<!--GLStatus:alle_Seiten-->54321<!---->bbb", GlStatus.alle_seiten(given, 54321))

    def test_korrigierte_seiten(self):
        given = "aaa<!--GLStatus:korrigierte_Seiten-->12345<!---->bbb"
        compare("aaa<!--GLStatus:korrigierte_Seiten-->54321<!---->bbb", GlStatus.korrigierte_seiten(given, 54321))

    def test_fertige_seiten(self):
        given = "aaa<!--GLStatus:fertige_Seiten-->1234<!---->bbb"
        compare("aaa<!--GLStatus:fertige_Seiten-->4321<!---->bbb", GlStatus.fertige_seiten(given, 4321))

    def test_year_some_pages_left(self):
        bot = GlStatus(None, False)
        with mock.patch.object(GlStatus, "petscan", side_effect=[50, 30, 20]):
            compare(
                '<!--GLStatus:1860-->|span style="background-color:#4876FF; '
                'font-weight: bold"|ca. 80,0 % korrigiert oder fertig<!---->',
                bot.year(1860, "<!--GLStatus:1860-->something<!---->"),
            )

    def test_year_rest_is_korrigiert(self):
        bot = GlStatus(None, False)
        with mock.patch.object(GlStatus, "petscan", side_effect=[50, 30, 0]):
            compare(
                '<!--GLStatus:1860-->|span style="background-color:#F7D700; '
                'font-weight: bold"|62,5 % fertig, Rest korrigiert<!---->',
                bot.year(1860, "<!--GLStatus:1860-->something<!---->"),
            )

    def test_year_all_done(self):
        bot = GlStatus(None, False)
        with mock.patch.object(GlStatus, "petscan", side_effect=[10, 0, 0]):
            compare(
                '<!--GLStatus:1860-->|span style="background-color:#00FF00; font-weight: bold"|Fertig<!---->',
                bot.year(1860, "<!--GLStatus:1860-->something<!---->"),
            )

    def test_petscan_pages(self):
        self.searcher_mock.run.return_value = ["a", "b", "c"]
        bot = GlStatus(None, False)
        compare(3, bot.petscan(["Fertig"]))
        self.searcher_mock.set_timeout.assert_called_once_with(120)
        self.searcher_mock.add_namespace.assert_called_once_with(102)
        self.searcher_mock.set_search_depth.assert_called_once_with(5)
        compare(
            [mock.call("Die Gartenlaube"), mock.call("Fertig")], self.searcher_mock.add_positive_category.call_args_list
        )
        self.searcher_mock.add_negative_category.assert_not_called()

    def test_petscan_articles_with_negative_categories(self):
        self.searcher_mock.run.return_value = []
        bot = GlStatus(None, False)
        compare(0, bot.petscan([], article=True, not_categories=["Die Gartenlaube Hefte"]))
        self.searcher_mock.add_namespace.assert_called_once_with(0)
        self.searcher_mock.add_negative_category.assert_called_once_with("Die Gartenlaube Hefte")

    def test_petscan_for_one_year(self):
        self.searcher_mock.run.return_value = ["a"]
        bot = GlStatus(None, False)
        compare(1, bot.petscan([], year=1860))
        self.searcher_mock.add_positive_category.assert_called_once_with("Die Gartenlaube (1860)")

    def test_task(self):
        self.page_mock.return_value.text = "<!--new line: Liste wird von einem Bot aktuell gehalten.-->"
        with (
            mock.patch.object(GlStatus, "petscan", return_value=7),
            GlStatus(wiki=None, debug=False, log_to_wiki=False) as bot,
        ):
            self.assertTrue(bot.run())
        compare("Die Gartenlaube", self.page_mock.call_args[0][1])
        self.page_mock.return_value.save.assert_called_once_with("Ein neuer Datensatz wurde eingefügt.", bot=True)

    def test_task_debug_uses_user_subpage(self):
        self.page_mock.return_value.text = "<!--new line: Liste wird von einem Bot aktuell gehalten.-->"
        with (
            mock.patch.object(GlStatus, "petscan", return_value=7),
            GlStatus(wiki=None, debug=True, log_to_wiki=False) as bot,
        ):
            self.assertTrue(bot.run())
        compare("Benutzer:THEbotIT/GlStatus", self.page_mock.call_args[0][1])
