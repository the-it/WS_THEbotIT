"""
Reverts the edits of the ReScanner (edit summary "ReScanner hat folgende Aufgaben bearbeitet: ...").

Every edit is undone with the MediaWiki undo function, so later edits of other users are kept. If the
undo conflicts with a later edit, the edit is skipped and reported. Edits that were already reverted
(revision tagged "mw-reverted", or a later revision restored the content before the edit) are skipped,
so the script can be run several times without reverting a revert.

Without --apply the script only reports what it would do.

uv run python -m service.ws_re.scanner.revert --start 2026-10-25T18:00:00Z --end 2026-10-26T06:00:00Z --task HLTS
"""

import argparse
import re
from collections.abc import Iterable
from dataclasses import dataclass

import pywikibot
from pywikibot.exceptions import APIError, EditConflictError

SUMMARY_PREFIX = "ReScanner hat folgende Aufgaben bearbeitet: "


@dataclass(frozen=True)
class ReScannerEdit:
    title: str
    revid: int
    parentid: int
    timestamp: str
    tasks: tuple[str, ...]
    tags: tuple[str, ...]


def parse_tasks(comment: str) -> tuple[str, ...] | None:
    """Tasks listed in a ReScanner edit summary, None if the summary isn't one of the ReScanner."""
    if not comment.startswith(SUMMARY_PREFIX):
        return None
    return tuple(task.strip() for task in comment[len(SUMMARY_PREFIX) :].split(","))


def is_already_reverted(edit: ReScannerEdit, parent_sha1: str | None, later_revisions: Iterable[dict]) -> bool:
    """
    The edit was undone, rolled back or manually reverted: the revision is tagged "mw-reverted", a later
    revision has the content before the edit, or a later edit summary says it undid this revision.
    """
    if "mw-reverted" in edit.tags:
        return True
    for revision in later_revisions:
        if parent_sha1 is not None and revision.get("sha1") == parent_sha1:
            return True
        comment = revision.get("comment", "")
        if re.search(rf"\b{edit.revid}\b", comment) and "rückgängig" in comment.lower():
            return True
    return False


class ReScannerReverter:
    def __init__(self, wiki: pywikibot.site.APISite, apply: bool = False, user: str = "THEbotIT"):
        self.wiki = wiki
        self.apply = apply
        self.user = user

    def find_edits(self, start: str, end: str, tasks: set[str] | None = None) -> list[ReScannerEdit]:
        """ReScanner edits between start and end (newest first), optionally only those containing one of tasks."""
        edits = []
        for contrib in self.wiki.usercontribs(
            user=self.user, start=end, end=start, prop="ids|title|timestamp|comment|tags"
        ):
            edit_tasks = parse_tasks(contrib.get("comment", ""))
            if edit_tasks is None:
                continue
            if tasks and not tasks & set(edit_tasks):
                continue
            edits.append(
                ReScannerEdit(
                    title=contrib["title"],
                    revid=contrib["revid"],
                    parentid=contrib["parentid"],
                    timestamp=contrib["timestamp"],
                    tasks=edit_tasks,
                    tags=tuple(contrib.get("tags", [])),
                )
            )
        return edits

    def _history_around(self, edit: ReScannerEdit) -> tuple[str | None, list[dict]]:
        """sha1 of the parent revision and all revisions after the edit."""
        response = self.wiki.simple_request(
            action="query",
            prop="revisions",
            titles=edit.title,
            rvstartid=edit.parentid,
            rvdir="newer",
            rvprop="ids|sha1|comment",
            rvlimit="max",
        ).submit()
        revisions = next(iter(response["query"]["pages"].values())).get("revisions", [])
        parent_sha1 = next((rev.get("sha1") for rev in revisions if rev["revid"] == edit.parentid), None)
        later_revisions = [rev for rev in revisions if rev["revid"] > edit.revid]
        return parent_sha1, later_revisions

    def revert(self, edit: ReScannerEdit, reason: str | None = None) -> str:
        """Undo a single edit, returns the outcome ("reverted", "would revert", "already reverted", ...)."""
        if not edit.parentid:
            return "skipped, page creation"
        parent_sha1, later_revisions = self._history_around(edit)
        if is_already_reverted(edit, parent_sha1, later_revisions):
            return "already reverted"
        if not self.apply:
            return "would revert"
        summary = f"Bearbeitung {edit.revid} des ReScanners ({', '.join(edit.tasks)}) rückgängig gemacht"
        if reason:
            summary = f"{summary}: {reason}"
        page = pywikibot.Page(self.wiki, edit.title)
        try:
            self.wiki.editpage(page, summary=summary, undo=edit.revid, minor=True, bot=True)
        except EditConflictError:
            return "conflict, later edits prevent the undo"
        except APIError as error:
            if error.code == "undofailure":
                return "conflict, later edits prevent the undo"
            return f"error: {error.code}"
        return "reverted"

    def run(self, start: str, end: str, tasks: set[str] | None = None, reason: str | None = None) -> dict[str, int]:
        stats: dict[str, int] = {}
        for edit in self.find_edits(start, end, tasks):
            outcome = self.revert(edit, reason)
            print(f"{edit.timestamp} [[{edit.title}]] {edit.revid} ({', '.join(edit.tasks)}): {outcome}")
            stats[outcome] = stats.get(outcome, 0) + 1
        print(stats)
        return stats


def main():  # pragma: no cover
    parser = argparse.ArgumentParser(description="Revert ReScanner edits.")
    parser.add_argument("--start", required=True, help="oldest edit timestamp, e.g. 2026-10-25T18:00:00Z")
    parser.add_argument("--end", default=None, help="newest edit timestamp, default: now")
    parser.add_argument("--task", action="append", help="only edits containing this task, repeatable, e.g. HLTS")
    parser.add_argument("--reason", default=None, help="appended to the edit summary")
    parser.add_argument("--user", default="THEbotIT")
    parser.add_argument("--apply", action="store_true", help="actually edit, otherwise dry run")
    args = parser.parse_args()
    wiki = pywikibot.Site(code="de", fam="wikisource", user=args.user)
    end = args.end or pywikibot.Timestamp.utcnow().isoformat()
    tasks = set(args.task) if args.task else None
    ReScannerReverter(wiki, apply=args.apply, user=args.user).run(args.start, end, tasks, args.reason)


if __name__ == "__main__":  # pragma: no cover
    main()
