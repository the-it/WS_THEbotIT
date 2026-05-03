# pragma: no cover

import json
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

from service.ws_re.register.repo import DataRepo
from service.ws_re.volumes import Volumes

LINE_HEIGHT = 20
LABEL_WIDTH = 80
LABEL_PADDING = 6

COLOR_GREEN = (102, 153, 102)
COLOR_YELLOW = (255, 215, 0)
COLOR_RED = (170, 0, 0)
COLOR_BLACK = (0, 0, 0)
COLOR_BACKGROUND = (255, 255, 255)
COLOR_TEXT = (0, 0, 0)

Color = Tuple[int, int, int]


def _color_for_proof_read(proof_read: Optional[int]) -> Color:
    if proof_read == 3:
        return COLOR_GREEN
    if proof_read == 2:
        return COLOR_YELLOW
    if proof_read in (0, 1):
        return COLOR_RED
    return COLOR_BLACK


def _build_row_articles(lemmas: List[dict], start_column: int, length: int) -> List[List[Color]]:
    spans: List[List] = []
    for lemma in lemmas:
        chapters = lemma.get("chapters", [])
        if not chapters:
            continue
        color = _color_for_proof_read(lemma.get("proof_read"))
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
        new_last = volume_end
        for j in range(i + 1, len(spans)):
            if spans[j][0] > span[1]:
                new_last = spans[j][0] - 1
                break
        span[1] = new_last

    articles_per_column: List[List[Color]] = [[] for _ in range(length)]
    for first, last, color, _ in spans:
        for column in range(first, last + 1):
            idx = column - start_column
            if 0 <= idx < length:
                articles_per_column[idx].append(color)
    return articles_per_column


def _load_font() -> ImageFont.ImageFont:
    for candidate in ("DejaVuSans.ttf", "Arial.ttf", "Helvetica.ttf"):
        try:
            return ImageFont.truetype(candidate, 13)
        except OSError:
            continue
    return ImageFont.load_default()


def create_picture(output_path: Path) -> None:
    data_path = DataRepo().get_data_path()
    rows: List[Tuple[str, List[List[Color]]]] = []
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
        rows.append((volume.name, _build_row_articles(lemmas, start_column, length)))

    bar_width = max(len(row) for _, row in rows)
    width = LABEL_WIDTH + bar_width
    height = len(rows) * LINE_HEIGHT
    image = Image.new("RGB", (width, height), COLOR_BACKGROUND)
    pixels = image.load()
    assert pixels is not None
    for row_idx, (_, articles_per_column) in enumerate(rows):
        row_y = row_idx * LINE_HEIGHT
        for col_idx, article_colors in enumerate(articles_per_column):
            x = LABEL_WIDTH + col_idx
            if not article_colors:
                for y_offset in range(LINE_HEIGHT):
                    pixels[x, row_y + y_offset] = COLOR_BLACK
                continue
            count = len(article_colors)
            for i, color in enumerate(article_colors):
                y_start = (i * LINE_HEIGHT) // count
                y_end = ((i + 1) * LINE_HEIGHT) // count
                for y_offset in range(y_start, y_end):
                    pixels[x, row_y + y_offset] = color

    draw = ImageDraw.Draw(image)
    font = _load_font()
    for row_idx, (name, _) in enumerate(rows):
        draw.text(
            (LABEL_PADDING, row_idx * LINE_HEIGHT + (LINE_HEIGHT - 13) // 2),
            name,
            fill=COLOR_TEXT,
            font=font,
        )

    image.save(output_path)


if __name__ == "__main__":
    create_picture(Path(__file__).parent.joinpath("proof_read_overview.png"))
