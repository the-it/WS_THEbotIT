# pylint: disable=protected-access
from dataclasses import replace
from unittest import TestCase, mock

from pywikibot.exceptions import APIError
from testfixtures import compare

from service.ws_re.scanner.revert import ReScannerEdit, ReScannerReverter, is_already_reverted, parse_tasks

EDIT = ReScannerEdit(
    title="RE:Pindaros 2",
    revid=5082599,
    parentid=5080000,
    timestamp="2026-10-26T02:00:00Z",
    tasks=("HLTS",),
    tags=(),
)


def contrib(comment: str, revid: int = 2, parentid: int = 1, tags: list[str] | None = None) -> dict:
    return {
        "title": "RE:Aal",
        "revid": revid,
        "parentid": parentid,
        "timestamp": "2026-10-26T02:00:00Z",
        "comment": comment,
        "tags": tags or [],
    }


def history(revisions: list[dict]) -> mock.Mock:
    request = mock.Mock()
    request.submit.return_value = {"query": {"pages": {"1": {"revisions": revisions}}}}
    return request


class TestParseTasks(TestCase):
    def test_rescanner_summary(self):
        compare(("BASE", "HLTS"), parse_tasks("ReScanner hat folgende Aufgaben bearbeitet: BASE, HLTS"))

    def test_other_summary(self):
        compare(None, parse_tasks("Bearbeitung 123 rückgängig gemacht"))
        compare(None, parse_tasks(""))


class TestIsAlreadyReverted(TestCase):
    def test_not_reverted(self):
        self.assertFalse(is_already_reverted(EDIT, "parent", [{"sha1": "other", "comment": "irgendwas"}]))

    def test_no_later_revisions(self):
        self.assertFalse(is_already_reverted(EDIT, "parent", []))

    def test_tagged_reverted(self):
        edit = replace(EDIT, tags=("mw-reverted",))
        self.assertTrue(is_already_reverted(edit, "parent", []))

    def test_later_revision_restores_parent_content(self):
        self.assertTrue(is_already_reverted(EDIT, "parent", [{"sha1": "other"}, {"sha1": "parent"}]))

    def test_later_summary_undoes_revision(self):
        later = [{"sha1": "merged", "comment": "Änderung 5082599 von THEbotIT rückgängig gemacht"}]
        self.assertTrue(is_already_reverted(EDIT, "parent", later))

    def test_later_summary_with_other_revid_does_not_count(self):
        later = [{"sha1": "merged", "comment": "Änderung 50825990 von THEbotIT rückgängig gemacht"}]
        self.assertFalse(is_already_reverted(EDIT, "parent", later))

    def test_missing_parent_sha1_is_no_match(self):
        self.assertFalse(is_already_reverted(EDIT, None, [{}]))


class TestReScannerReverter(TestCase):
    def setUp(self):
        self.wiki = mock.Mock()

    def test_find_edits_filters_summary_and_tasks(self):
        self.wiki.usercontribs.return_value = [
            contrib("ReScanner hat folgende Aufgaben bearbeitet: BASE, HLTS", revid=10, tags=["mw-reverted"]),
            contrib("ReScanner hat folgende Aufgaben bearbeitet: KURZ", revid=11),
            contrib("Anderer Bot-Lauf", revid=12),
        ]
        reverter = ReScannerReverter(self.wiki)

        compare([10, 11], [edit.revid for edit in reverter.find_edits("start", "end")])
        edits = reverter.find_edits("start", "end", {"HLTS"})
        compare([10], [edit.revid for edit in edits])
        compare(("BASE", "HLTS"), edits[0].tasks)
        compare(("mw-reverted",), edits[0].tags)
        self.wiki.usercontribs.assert_called_with(
            user="THEbotIT", start="end", end="start", prop="ids|title|timestamp|comment|tags"
        )

    def test_dry_run_does_not_edit(self):
        self.wiki.simple_request.return_value = history(
            [{"revid": 5080000, "sha1": "parent"}, {"revid": 5082599, "sha1": "bot"}]
        )
        compare("would revert", ReScannerReverter(self.wiki).revert(EDIT))
        self.wiki.editpage.assert_not_called()

    @mock.patch("service.ws_re.scanner.revert.pywikibot.Page")
    def test_apply_undoes_revision(self, page_mock):
        self.wiki.simple_request.return_value = history(
            [{"revid": 5080000, "sha1": "parent"}, {"revid": 5082599, "sha1": "bot"}]
        )
        compare("reverted", ReScannerReverter(self.wiki, apply=True).revert(EDIT, "Anker-Bug"))
        self.wiki.editpage.assert_called_once_with(
            page_mock.return_value,
            summary="Bearbeitung 5082599 des ReScanners (HLTS) rückgängig gemacht: Anker-Bug",
            undo=5082599,
            minor=True,
            bot=True,
        )

    def test_already_reverted_does_not_edit(self):
        self.wiki.simple_request.return_value = history(
            [
                {"revid": 5080000, "sha1": "parent"},
                {"revid": 5082599, "sha1": "bot"},
                {"revid": 5090000, "sha1": "parent"},
            ]
        )
        compare("already reverted", ReScannerReverter(self.wiki, apply=True).revert(EDIT))
        self.wiki.editpage.assert_not_called()

    def test_own_revert_is_recognised(self):
        # a revert of this script, 3-way merged with a later edit, doesn't restore the parent sha1
        self.wiki.simple_request.return_value = history(
            [
                {"revid": 5080000, "sha1": "parent"},
                {"revid": 5082599, "sha1": "bot"},
                {"revid": 5085000, "sha1": "other", "comment": "Korrektur"},
                {
                    "revid": 5090000,
                    "sha1": "merged",
                    "comment": "Bearbeitung 5082599 des ReScanners (HLTS) rückgängig gemacht",
                },
            ]
        )
        compare("already reverted", ReScannerReverter(self.wiki, apply=True).revert(EDIT))
        self.wiki.editpage.assert_not_called()

    @mock.patch("service.ws_re.scanner.revert.pywikibot.Page")
    def test_undo_conflict_is_reported(self, _):
        self.wiki.simple_request.return_value = history([{"revid": 5080000, "sha1": "parent"}])
        self.wiki.editpage.side_effect = APIError("undofailure", "conflict")
        compare("conflict, later edits prevent the undo", ReScannerReverter(self.wiki, apply=True).revert(EDIT))

    def test_page_creation_is_skipped(self):
        edit = replace(EDIT, parentid=0)
        compare("skipped, page creation", ReScannerReverter(self.wiki, apply=True).revert(edit))
        self.wiki.simple_request.assert_not_called()

    def test_run_counts_outcomes(self):
        self.wiki.usercontribs.return_value = [
            contrib("ReScanner hat folgende Aufgaben bearbeitet: HLTS", revid=10, tags=["mw-reverted"]),
            contrib("ReScanner hat folgende Aufgaben bearbeitet: HLTS", revid=11),
        ]
        self.wiki.simple_request.return_value = history([{"revid": 1, "sha1": "parent"}])
        compare(
            {"already reverted": 1, "would revert": 1},
            ReScannerReverter(self.wiki).run("start", "end", {"HLTS"}),
        )
