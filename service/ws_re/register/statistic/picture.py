import tempfile
from datetime import date, datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pywikibot import FilePage
from pywikibot.exceptions import APIError
from pywikibot.site import BaseSite

from service.ws_re.register.authors import Authors
from service.ws_re.register.statistic.base import (
    AREA_OPACITY,
    CHART_PALETTE,
    SUMMARY,
    Color,
    hex_to_rgb,
    history_entries,
    lemmas_per_column,
    load_volume_lemmas,
    mix_with_white,
    state_at,
)
from tools.bots.logger import WikiLogger

LINE_HEIGHT = 20
LABEL_WIDTH = 80
LABEL_PADDING = 6
HEADER_HEIGHT = 8
COLUMN_GRID_INTERVAL = 50
COLUMN_LABEL_FONT_SIZE = 7

# the states have the colors of their series in the history charts
COLOR_ERFASST = hex_to_rgb(CHART_PALETTE[0])
COLOR_KORRIGIERT = hex_to_rgb(CHART_PALETTE[1])
COLOR_UNKORRIGIERT = hex_to_rgb(CHART_PALETTE[2])
COLOR_FERTIG = hex_to_rgb(CHART_PALETTE[3])
# erfasst articles, that are not in the public domain yet, get a lighter tone of COLOR_ERFASST. The tone is the area
# color of the chart for articles entering the public domain next year and fades to OPACITY_PROTECTED_LATEST for
# articles entering it in PROTECTED_GRADIENT_YEARS years or later.
OPACITY_PROTECTED_LATEST = 0.15
PROTECTED_GRADIENT_YEARS = 60
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_BACKGROUND = (255, 255, 255)
COLOR_TEXT = (0, 0, 0)
# width / height of the picture of a single volume, the ratio of the picture of all volumes
VOLUME_PICTURE_RATIO = 2038 / 2352

# label of the line, first column of the line, colors of the articles of every column of the line
Row = tuple[str, int, list[list[Color]]]


class ProofReadPicture:
    """Picture of the proof read state of every column of every volume, uploaded to wikisource."""

    @staticmethod
    def file_name(year: int) -> str:
        """Every year gets its own picture on wikisource, showing the state of the day of the last upload."""
        return f"Pauly-Wissowa stats overview {year}.png"

    def __init__(self, wiki: BaseSite, logger: WikiLogger, day: date | None = None):
        """
        :param day: the picture shows the proof read state of every lemma at the end of this day, default today.
            The years to the public domain count from the year of the day too.
        """
        self.wiki = wiki
        self.logger = logger
        self.authors = Authors()
        self.day = day or datetime.now().date()

    @staticmethod
    def volume_file_name(volume_name: str) -> str:
        """The picture of a single volume on wikisource, showing the state of the day of the last upload."""
        return f"Pauly-Wissowa stats overview {volume_name}.png"

    def update(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir).joinpath("proof_read_overview.png")
            self.logger.info("Generate proof-read overview picture.")
            self.create(output_path)
            self._upload(output_path, self.file_name(self.day.year))

    def update_volume(self, volume_name: str) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir).joinpath("proof_read_volume.png")
            self.logger.info(f"Generate proof-read picture of {volume_name}.")
            self.create_volume(volume_name, output_path)
            self._upload(output_path, self.volume_file_name(volume_name))

    def _upload(self, output_path: Path, file_name: str) -> None:
        self.logger.info(f"Upload {file_name} to wikisource.")
        file_page = FilePage(self.wiki, f"File:{file_name}")
        try:
            file_page.upload(str(output_path), comment=SUMMARY, ignore_warnings=True)
        except APIError as error:
            # the API refuses an upload identical to the current version, the picture is up to date then
            if error.code != "fileexists-no-change":
                raise
            self.logger.info(f"{file_name} is up to date.")

    def _public_domain_year(self, lemma: dict, volume_name: str) -> int:
        """The year the lemma enters the public domain, 0 if it has no known authors or no creative height."""
        if lemma.get("no_creative_height"):
            return 0
        max_pd_year = 0
        for chapter in lemma.get("chapters", []):
            author_name = chapter.get("author")
            if not author_name:
                continue
            for mapped in self.authors.get_author_by_mapping(author_name, volume_name):
                if mapped.year_public_domain:
                    max_pd_year = max(max_pd_year, mapped.year_public_domain)
        return max_pd_year

    @staticmethod
    def _color_protected(years_to_public_domain: int) -> Color:
        """
        Color of an erfasst article, that enters the public domain in the given number of years (at least 1). The
        later it enters the public domain, the lighter the color.
        """
        fade = min(max(years_to_public_domain - 1, 0) / (PROTECTED_GRADIENT_YEARS - 1), 1.0)
        return mix_with_white(CHART_PALETTE[0], AREA_OPACITY - fade * (AREA_OPACITY - OPACITY_PROTECTED_LATEST))

    def _color_for_lemma(self, lemma: dict, volume_name: str) -> Color:
        proof_read = state_at(history_entries(lemma), self.day)
        if proof_read == 3:
            return COLOR_FERTIG
        if proof_read == 2:
            return COLOR_KORRIGIERT
        if proof_read == 1:
            return COLOR_UNKORRIGIERT
        if proof_read == 0:
            years_to_public_domain = self._public_domain_year(lemma, volume_name) - self.day.year
            if years_to_public_domain > 0:
                return self._color_protected(years_to_public_domain)
            return COLOR_ERFASST
        return COLOR_BLACK

    def _build_row_articles(
        self, lemmas: list[dict], start_column: int, length: int, volume_name: str
    ) -> list[list[Color]]:
        colors: dict[int, Color] = {}
        articles_per_column: list[list[Color]] = []
        for indices in lemmas_per_column(lemmas, start_column, length):
            for index in indices:
                if index not in colors:
                    colors[index] = self._color_for_lemma(lemmas[index], volume_name)
            articles_per_column.append([colors[index] for index in indices])
        return articles_per_column

    @staticmethod
    def _load_font(size: int = 13) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        for candidate in ("DejaVuSans.ttf", "Arial.ttf", "Helvetica.ttf"):
            try:
                return ImageFont.truetype(candidate, size)
            except OSError:
                continue
        return ImageFont.load_default_imagefont()

    @staticmethod
    def _gridline_count(start: int, length: int) -> int:
        # Count of marked columns c (multiples of COLUMN_GRID_INTERVAL) strictly
        # after start, up to start + length - 1. A gridline gap is inserted just
        # before each such column, so this also equals the number of inserted
        # gap pixels for the row.
        end = start + length - 1
        return end // COLUMN_GRID_INTERVAL - start // COLUMN_GRID_INTERVAL

    def create(self, output_path: Path) -> None:
        """Picture of all volumes, one line per volume, every column one pixel wide."""
        rows: list[Row] = []
        for volume, lemmas in load_volume_lemmas():
            start_column = volume.start_column
            end_column = volume.end_column
            if start_column is None or end_column is None:
                continue
            length = end_column - start_column + 1
            rows.append(
                (
                    volume.name,
                    start_column,
                    self._build_row_articles(lemmas, start_column, length, volume.name),
                )
            )
        self._draw(rows, output_path, 1)

    def create_volume(self, volume_name: str, output_path: Path) -> None:
        """
        Picture of a single volume. The line of the volume is broken into lines of COLUMN_GRID_INTERVAL columns on top of
        each other, starting with the first column of the volume. Every line is labeled with its first column, there are
        no gridlines. The columns are widened, so the picture gets the ratio of the picture of all volumes
        (VOLUME_PICTURE_RATIO).
        """
        for volume, lemmas in load_volume_lemmas():
            if volume.name != volume_name:
                continue
            if volume.start_column is None or volume.end_column is None:
                raise ValueError(f"The columns of {volume_name} are unknown.")
            length = volume.end_column - volume.start_column + 1
            articles = self._build_row_articles(lemmas, volume.start_column, length, volume.name)
            rows: list[Row] = [
                (
                    str(volume.start_column + offset),
                    volume.start_column + offset,
                    articles[offset : offset + COLUMN_GRID_INTERVAL],
                )
                for offset in range(0, length, COLUMN_GRID_INTERVAL)
            ]
            height = len(rows) * (HEADER_HEIGHT + LINE_HEIGHT)
            column_width = max(1, round((VOLUME_PICTURE_RATIO * height - LABEL_WIDTH) / COLUMN_GRID_INTERVAL))
            self._draw(rows, output_path, column_width, gridlines=False)
            return
        raise ValueError(f"There is no register of {volume_name}.")

    def _draw(self, rows: list[Row], output_path: Path, column_width: int, gridlines: bool = True) -> None:
        bar_width = max(
            len(articles) * column_width + (self._gridline_count(start, len(articles)) if gridlines else 0)
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
        font = self._load_font()
        header_font = self._load_font(COLUMN_LABEL_FONT_SIZE)

        for row_idx, (name, start_column, articles_per_column) in enumerate(rows):
            header_y = row_idx * row_block
            bar_y = header_y + HEADER_HEIGHT

            bar_offset = 0
            gridline_positions: list[tuple[int, int]] = []
            for col_idx, article_colors in enumerate(articles_per_column):
                c = start_column + col_idx
                if gridlines and col_idx > 0 and c % COLUMN_GRID_INTERVAL == 0:
                    gridline_positions.append((c, bar_offset))
                    bar_offset += 1
                for x in range(LABEL_WIDTH + bar_offset, LABEL_WIDTH + bar_offset + column_width):
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
                bar_offset += column_width

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
