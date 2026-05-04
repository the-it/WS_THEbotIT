import json
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont

from service.ws_re.register.authors import Authors
from service.ws_re.register.repo import DataRepo
from service.ws_re.volumes import Volumes

LINE_HEIGHT = 20
LABEL_WIDTH = 80
LABEL_PADDING = 6
HEADER_HEIGHT = 8
COLUMN_GRID_INTERVAL = 50
COLUMN_LABEL_FONT_SIZE = 7

COLOR_GREEN = (102, 153, 102)
COLOR_YELLOW = (255, 215, 0)
COLOR_RED = (170, 0, 0)
COLOR_LIGHT_RED = (255, 130, 130)
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_BACKGROUND = (255, 255, 255)
COLOR_TEXT = (0, 0, 0)

Color = Tuple[int, int, int]


def _is_public_domain(lemma: dict, authors: Authors, volume_name: str) -> bool:
    if lemma.get("no_creative_height"):
        return True
    max_pd_year = 0
    for chapter in lemma.get("chapters", []):
        author_name = chapter.get("author")
        if not author_name:
            continue
        for mapped in authors.get_author_by_mapping(author_name, volume_name):
            if mapped.year_public_domain:
                max_pd_year = max(max_pd_year, mapped.year_public_domain)
    if max_pd_year == 0:
        return True
    return max_pd_year <= datetime.now().year


def _color_for_lemma(lemma: dict, authors: Authors, volume_name: str) -> Color:
    proof_read = lemma.get("proof_read")
    if proof_read == 3:
        return COLOR_GREEN
    if proof_read == 2:
        return COLOR_YELLOW
    if proof_read in (0, 1):
        if not _is_public_domain(lemma, authors, volume_name):
            return COLOR_LIGHT_RED
        return COLOR_RED
    return COLOR_BLACK


def _build_row_articles(lemmas: List[dict], start_column: int, length: int,
                        authors: Authors, volume_name: str) -> List[List[Color]]:
    spans: List[List] = []
    for lemma in lemmas:
        chapters = lemma.get("chapters", [])
        if not chapters:
            continue
        color = _color_for_lemma(lemma, authors, volume_name)
        first = min(chapter["start"] for chapter in chapters)
        last = max(chapter.get("end", chapter["start"]) for chapter in chapters)
        last_chapter = max(chapters, key=lambda chapter: chapter["start"])
        open_ended = last_chapter.get("end") is None
        spans.append([first, last, color, open_ended])

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

    articles_per_column: List[List[Color]] = [[] for _ in range(length)]
    for first, last, color, _ in spans:
        for column in range(first, last + 1):
            idx = column - start_column
            if 0 <= idx < length:
                articles_per_column[idx].append(color)
    return articles_per_column


def _load_font(size: int = 13) -> ImageFont.ImageFont:
    for candidate in ("DejaVuSans.ttf", "Arial.ttf", "Helvetica.ttf"):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def create_picture(output_path: Path) -> None:
    data_path = DataRepo().get_data_path()
    authors = Authors()
    rows: List[Tuple[str, int, List[List[Color]]]] = []
    for volume in Volumes().all_volumes:
        start_column = volume.start_column
        end_column = volume.end_column
        if start_column is None or end_column is None:
            continue
        json_file = data_path.joinpath(f"{volume.file_name}.json")
        if not json_file.exists():
            continue
        with open(json_file, "r", encoding="utf-8") as fp:
            lemmas = json.load(fp)
        length = end_column - start_column + 1
        rows.append((
            volume.name,
            start_column,
            _build_row_articles(lemmas, start_column, length, authors, volume.name),
        ))

    def _gridline_count(start: int, length: int) -> int:
        # Count of marked columns c (multiples of COLUMN_GRID_INTERVAL) strictly
        # after start, up to start + length - 1. A gridline gap is inserted just
        # before each such column, so this also equals the number of inserted
        # gap pixels for the row.
        end = start + length - 1
        return end // COLUMN_GRID_INTERVAL - start // COLUMN_GRID_INTERVAL

    bar_width = max(
        len(articles) + _gridline_count(start, len(articles))
        for _, start, articles in rows
    )
    row_block = HEADER_HEIGHT + LINE_HEIGHT
    width = LABEL_WIDTH + bar_width
    height = len(rows) * row_block
    bar_height = LINE_HEIGHT - 1
    image = Image.new("RGB", (width, height), COLOR_BACKGROUND)
    pixels = image.load()
    assert pixels is not None

    draw = ImageDraw.Draw(image)
    font = _load_font()
    header_font = _load_font(COLUMN_LABEL_FONT_SIZE)

    for row_idx, (name, start_column, articles_per_column) in enumerate(rows):
        header_y = row_idx * row_block
        bar_y = header_y + HEADER_HEIGHT

        bar_offset = 0
        gridline_positions: List[Tuple[int, int]] = []
        for col_idx, article_colors in enumerate(articles_per_column):
            c = start_column + col_idx
            if col_idx > 0 and c % COLUMN_GRID_INTERVAL == 0:
                gridline_positions.append((c, bar_offset))
                bar_offset += 1
            x = LABEL_WIDTH + bar_offset
            if not article_colors:
                for y_offset in range(bar_height):
                    pixels[x, bar_y + y_offset] = COLOR_BLACK
            else:
                count = len(article_colors)
                for i, color in enumerate(article_colors):
                    y_start = (i * bar_height) // count
                    y_end = ((i + 1) * bar_height) // count
                    for y_offset in range(y_start, y_end):
                        pixels[x, bar_y + y_offset] = color
            bar_offset += 1

        draw.text(
            (LABEL_PADDING, bar_y + (LINE_HEIGHT - 13) // 2),
            name,
            fill=COLOR_TEXT,
            font=font,
        )
        for column, gap_offset in gridline_positions:
            x = LABEL_WIDTH + gap_offset
            text = str(column)
            text_bbox = draw.textbbox((0, 0), text, font=header_font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            text_x = x - text_width // 2
            text_y = header_y + (HEADER_HEIGHT - text_height) // 2 - text_bbox[1]
            draw.text((text_x, text_y), text, fill=COLOR_TEXT, font=header_font)

    image.save(output_path)


if __name__ == "__main__":
    create_picture(Path(__file__).parent.joinpath("proof_read_overview.png"))
