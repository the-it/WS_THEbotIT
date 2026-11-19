import json
from collections.abc import Generator
from datetime import date
from pathlib import Path
from string import Template

from pywikibot import Page

from service.ws_re.register.repo import DataRepo
from service.ws_re.volumes import Volume, Volumes
from tools.bots.logger import WikiLogger

SUMMARY = "Bearbeitungsstand aktualisiert"
# past years, that get a statistic page with charts and a picture of the proof read state at their end
PAST_YEARS = (2007, 2020, 2025)
# volumes, that get a statistic page with charts and a picture of the proof read state of their columns
STATISTIC_VOLUMES = ("I,1", "VIII,1", "S III")
TEMPLATE_PATH = Path(__file__).parent.joinpath("templates")
# palette of the chart renderer of Extension:Chart (theme "categorical"), the n-th series of a chart gets the n-th
# color. The picture uses the same colors.
CHART_PALETTE = ("#4b77d6", "#eeb533", "#fd7865", "#80cdb3", "#269f4b", "#b0c1f0", "#9182c2", "#d9b4cd")
# the chart renderer fills the areas with the color of the series at this opacity
AREA_OPACITY = 0.7

Color = tuple[int, int, int]


def hex_to_rgb(color: str) -> Color:
    """Converts a color like #4b77d6 to its channels (red, green, blue)."""
    return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)


def mix_with_white(color: str, opacity: float) -> Color:
    """The color drawn at the opacity on a white background."""
    red, green, blue = (round(channel * opacity + 255 * (1 - opacity)) for channel in hex_to_rgb(color))
    return red, green, blue


def render_template(file_name: str, **values: str) -> str:
    """Reads a file of the templates folder and substitutes its placeholders (${name}) with the values."""
    return Template(TEMPLATE_PATH.joinpath(file_name).read_text(encoding="utf-8")).substitute(values)


def parse_datestamp(datestamp: str) -> date:
    """Converts a datestamp of the history (format yymmdd) to a date."""
    return date(2000 + int(datestamp[0:2]), int(datestamp[2:4]), int(datestamp[4:6]))


def history_entries(lemma: dict) -> list[tuple[date, int]]:
    """
    The history of a lemma records the date each proof read state was entered. If the lemma dropped back to a lower
    state, the higher states were deleted.

    :return: entries of the history as (date, state) sorted chronologically
    """
    history = lemma.get("history") or {}
    return sorted((parse_datestamp(datestamp), int(state)) for state, datestamp in history.items())


def state_at(entries: list[tuple[date, int]], day: date) -> int | None:
    """
    The state at a given day is the state of the latest entry of the history up to that day.

    :param entries: entries of the history, see history_entries
    :return: the state at the day, None if the article didn't exist at that day
    """
    state = None
    for entry_date, entry_state in entries:
        if entry_date > day:
            break
        state = entry_state
    return state


def current_state(lemma: dict) -> int | None:
    """The current proof read state of the lemma according to its history, None if the article doesn't exist."""
    return state_at(history_entries(lemma), date.max)


def load_volume_lemmas() -> Generator[tuple[Volume, list[dict]]]:
    """Yields every volume together with the lemmas of its register, volumes without a register are skipped."""
    data_path = DataRepo().get_data_path()
    for volume in Volumes().all_volumes:
        json_file = data_path.joinpath(f"{volume.file_name}.json")
        if not json_file.exists():
            continue
        with open(json_file, "r", encoding="utf-8") as fp:
            yield volume, json.load(fp)


def lemmas_per_column(lemmas: list[dict], start_column: int, length: int) -> list[list[int]]:
    """
    Distributes the lemmas of a volume over its columns. A lemma spans from the first start to the last end of its
    chapters. If its last chapter has no end, the lemma extends up to the column before the next lemma.

    :param start_column: first column of the volume
    :param length: number of columns of the volume
    :return: for every column of the volume the indices of the lemmas (in lemmas) on that column
    """
    spans: list[list] = []
    for index, lemma in enumerate(lemmas):
        chapters = lemma.get("chapters", [])
        if not chapters:
            continue
        first = min(chapter["start"] for chapter in chapters)
        last = max(chapter.get("end", chapter["start"]) for chapter in chapters)
        last_chapter = max(chapters, key=lambda chapter: chapter["start"])
        open_ended = last_chapter.get("end") is None
        spans.append([first, last, index, open_ended])

    spans.sort(key=lambda span: span[0])
    volume_end = start_column + length - 1
    for i, span in enumerate(spans):
        if not span[3]:
            continue
        original_last = span[1]
        new_last = volume_end
        for j in range(i + 1, len(spans)):
            if spans[j][0] > original_last:
                new_last = spans[j][0] - 1
                break
        # An open-ended chapter must not extend into the body of a closed article whose
        # span already covers the column right after the open chapter — even when that
        # closed article appears earlier in sort order (same start column).
        for other in spans:
            if other is span or other[3]:
                continue
            if other[0] <= new_last and other[1] >= original_last + 1:
                new_last = min(new_last, other[0] - 1)
        span[1] = max(original_last, new_last)

    lemmas_of_column: list[list[int]] = [[] for _ in range(length)]
    for first, last, index, _ in spans:
        for column in range(first, last + 1):
            idx = column - start_column
            if 0 <= idx < length:
                lemmas_of_column[idx].append(index)
    return lemmas_of_column


def save_page(page: Page, text: str, logger: WikiLogger) -> None:
    """Saves the text to the page, if it differs from the current text."""
    # MediaWiki strips trailing whitespace on save
    if page.exists() and page.text.rstrip() == text.rstrip():
        logger.info(f"{page.title()} is up to date.")
        return
    logger.info(f"Update {page.title()}.")
    page.text = text
    page.save(SUMMARY, bot=True)


def save_json_page(page: Page, content: dict, logger: WikiLogger) -> None:
    """Saves the content as JSON to the page, if it differs from the current content (formatting is ignored)."""
    if page.exists():
        try:
            if json.loads(page.text) == content:
                logger.info(f"{page.title()} is up to date.")
                return
        except json.JSONDecodeError:
            pass
    save_page(page, json.dumps(content, ensure_ascii=False, indent=1), logger)
