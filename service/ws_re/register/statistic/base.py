import json
from collections.abc import Generator
from pathlib import Path
from string import Template

from pywikibot import Page

from service.ws_re.register.repo import DataRepo
from service.ws_re.volumes import Volume, Volumes
from tools.bots.logger import WikiLogger

SUMMARY = "Bearbeitungsstand aktualisiert"
TEMPLATE_PATH = Path(__file__).parent.joinpath("templates")


def render_template(file_name: str, **values: str) -> str:
    """Reads a file of the templates folder and substitutes its placeholders (${name}) with the values."""
    return Template(TEMPLATE_PATH.joinpath(file_name).read_text(encoding="utf-8")).substitute(values)


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
