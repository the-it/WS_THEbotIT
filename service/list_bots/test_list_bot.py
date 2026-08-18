# pylint: disable=protected-access
from typing import ClassVar
from unittest import mock

from testfixtures import LogCapture, compare

from service.list_bots.list_bot import ListBot
from tools.bots.test_base import TestCloudBase
from tools.petscan import PetScan
from tools.test import PageMock

STATIC_LIST_TEXT = "date line".ljust(150) + "static part of the list"


class DummyListBot(ListBot):
    LIST_LEMMA = "Liste der Dummies"
    PROPERTY_TEMPLATE = "Personendaten"
    PROPERTY_MAPPING: ClassVar[dict[str, str]] = {"name": "NAME"}

    def sort_to_list(self) -> list[dict[str, str]]:
        return [self.data[key] for key in self.data]

    def print_list(self, item_list: list[dict[str, str]]) -> str:
        return STATIC_LIST_TEXT

    def get_searcher(self) -> PetScan:
        return PetScan()


class TestListBot(TestCloudBase):
    def setUp(self):
        self.page_patcher = mock.patch("service.list_bots.list_bot.Page", new_callable=mock.MagicMock)
        self.page_mock = self.page_patcher.start()
        self.addCleanup(mock.patch.stopall)

    def tearDown(self):
        mock.patch.stopall()
        super().tearDown()

    def test_get_searcher(self):
        self.assertIsInstance(DummyListBot().get_searcher(), PetScan)

    def test_get_page_infos(self):
        page = PageMock()
        page.text = "{{Personendaten\n|NAME=Ein Dummy\n}}"
        compare({"name": "Ein Dummy"}, DummyListBot().get_page_infos(page))

    def test_task_keeps_the_page_when_only_the_date_changed(self):
        self.page_mock.return_value.text = "intro\n" + STATIC_LIST_TEXT
        with (
            mock.patch.object(DummyListBot, "process_lemmas"),
            LogCapture() as log_catcher,
            DummyListBot(log_to_screen=False, log_to_wiki=False) as bot,
        ):
            self.assertTrue(bot.run())
        log_catcher.check_present(
            ("DummyListBot", "INFO", "Heute gab es keine Änderungen, daher wird die Seite nicht überschrieben.")
        )
        self.page_mock.return_value.save.assert_not_called()

    def test_task_saves_a_changed_list(self):
        self.page_mock.return_value.text = "a completely different list"
        with (
            mock.patch.object(DummyListBot, "process_lemmas"),
            DummyListBot(log_to_screen=False, log_to_wiki=False) as bot,
        ):
            self.assertTrue(bot.run())
        self.page_mock.return_value.save.assert_called_once_with(
            "Die Liste wurde auf den aktuellen Stand gebracht.", bot=True
        )

    def test_process_lemmas_stops_on_watchdog(self):
        lemmas = [f":Lemma{idx}" for idx in range(60)]
        with (
            mock.patch.object(DummyListBot, "get_combined_lemma_list", mock.Mock(return_value=(lemmas, 0))),
            mock.patch.object(DummyListBot, "remove_old_lemmas"),
            mock.patch.object(DummyListBot, "get_page_infos", mock.Mock(return_value={})),
            mock.patch.object(DummyListBot, "_watchdog", mock.Mock(return_value=True)),
            DummyListBot(log_to_screen=False, log_to_wiki=False) as bot,
        ):
            bot.data.assign_dict({})
            bot.process_lemmas()
            # the watchdog is only asked after the 51st lemma, so everything before is processed
            compare(52, len(bot.data.keys()))

    def test_process_lemmas_logs_unparsable_lemmas(self):
        with (
            mock.patch.object(DummyListBot, "get_combined_lemma_list", mock.Mock(return_value=([":Lemma"], 1))),
            mock.patch.object(DummyListBot, "remove_old_lemmas"),
            mock.patch.object(DummyListBot, "get_page_infos", mock.Mock(side_effect=ValueError)),
            LogCapture() as log_catcher,
            DummyListBot(log_to_screen=False, log_to_wiki=False) as bot,
        ):
            bot.data.assign_dict({})
            bot.process_lemmas()
        log_catcher.check_present(("DummyListBot", "ERROR", "lemma Lemma was not parsed correctly."))
