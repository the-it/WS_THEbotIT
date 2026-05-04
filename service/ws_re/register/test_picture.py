# pylint: disable=protected-access,no-self-use
import json
import tempfile
from pathlib import Path
from unittest import mock

from PIL import Image, ImageFont
from testfixtures import compare

from service.ws_re.register.authors import Authors
from service.ws_re.register.picture import (
    COLOR_BLACK,
    COLOR_GREEN,
    COLOR_LIGHT_RED,
    COLOR_RED,
    COLOR_WHITE,
    COLOR_YELLOW,
    HEADER_HEIGHT,
    LABEL_WIDTH,
    LINE_HEIGHT,
    _build_row_articles,
    _color_for_lemma,
    _is_public_domain,
    _load_font,
    create_picture,
)
from service.ws_re.register.test_base import BaseTestRegister, copy_tst_data
from service.ws_re.volumes import Volume


class TestIsPublicDomain(BaseTestRegister):
    def setUp(self):
        self.authors = Authors()

    def test_no_creative_height_short_circuits(self):
        # year_public_domain of Herman Abel (death 1998) would be 2069 — would normally not be PD,
        # but no_creative_height bypasses the author check.
        lemma = {
            "no_creative_height": True,
            "chapters": [{"start": 1, "author": "Abel"}],
        }
        compare(True, _is_public_domain(lemma, self.authors, "I,1"))

    def test_no_chapters_returns_true(self):
        compare(True, _is_public_domain({"chapters": []}, self.authors, "I,1"))

    def test_chapter_without_author_returns_true(self):
        lemma = {"chapters": [{"start": 1}]}
        compare(True, _is_public_domain(lemma, self.authors, "I,1"))

    def test_unknown_author_treated_as_public_domain(self):
        # Unmapped author yields no Author objects, so max_pd_year stays 0 → True.
        lemma = {"chapters": [{"start": 1, "author": "Unknown"}]}
        compare(True, _is_public_domain(lemma, self.authors, "I,1"))

    def test_author_in_public_domain(self):
        # Abert death 1927 + 71 = 1998 ≤ current year → PD.
        lemma = {"chapters": [{"start": 1, "author": "Abert"}]}
        compare(True, _is_public_domain(lemma, self.authors, "I,1"))

    def test_author_not_in_public_domain(self):
        # Herman Abel death 1998 + 71 = 2069 > current year → not PD.
        lemma = {"chapters": [{"start": 1, "author": "Abel"}]}
        compare(False, _is_public_domain(lemma, self.authors, "I,1"))

    def test_max_year_is_used_across_chapters(self):
        # Abert (1998 PD) plus Abel (2069 PD) → max is 2069 → not PD.
        lemma = {
            "chapters": [
                {"start": 1, "author": "Abert"},
                {"start": 2, "author": "Abel"},
            ]
        }
        compare(False, _is_public_domain(lemma, self.authors, "I,1"))

    def test_volume_specific_mapping_is_respected(self):
        # For volume "XVI,1" the "Abel" mapping resolves to Abel_XVI,1 (death 1987 → PD 2058).
        lemma = {"chapters": [{"start": 1, "author": "Abel"}]}
        compare(False, _is_public_domain(lemma, self.authors, "XVI,1"))


class TestColorForLemma(BaseTestRegister):
    def setUp(self):
        self.authors = Authors()

    def test_proof_read_3_is_green(self):
        compare(COLOR_GREEN, _color_for_lemma({"proof_read": 3}, self.authors, "I,1"))

    def test_proof_read_2_is_yellow(self):
        compare(COLOR_YELLOW, _color_for_lemma({"proof_read": 2}, self.authors, "I,1"))

    def test_proof_read_1_public_domain_is_red(self):
        lemma = {"proof_read": 1, "no_creative_height": True}
        compare(COLOR_RED, _color_for_lemma(lemma, self.authors, "I,1"))

    def test_proof_read_0_public_domain_is_red(self):
        lemma = {"proof_read": 0, "no_creative_height": True}
        compare(COLOR_RED, _color_for_lemma(lemma, self.authors, "I,1"))

    def test_proof_read_1_not_public_domain_is_light_red(self):
        lemma = {"proof_read": 1, "chapters": [{"start": 1, "author": "Abel"}]}
        compare(COLOR_LIGHT_RED, _color_for_lemma(lemma, self.authors, "I,1"))

    def test_missing_proof_read_falls_through_to_black(self):
        compare(COLOR_BLACK, _color_for_lemma({}, self.authors, "I,1"))


class TestBuildRowArticles(BaseTestRegister):
    def setUp(self):
        self.authors = Authors()

    def test_skips_lemmas_without_chapters(self):
        result = _build_row_articles([{"chapters": []}], 1, 3, self.authors, "I,1")
        compare([[], [], []], result)

    def test_assigns_color_to_columns_in_span(self):
        lemma = {
            "proof_read": 3,
            "chapters": [{"start": 2, "end": 3, "author": "Abert"}],
        }
        result = _build_row_articles([lemma], 1, 5, self.authors, "I,1")
        compare([[], [COLOR_GREEN], [COLOR_GREEN], [], []], result)

    def test_uses_start_when_end_missing_and_no_following_span(self):
        # Open-ended last chapter with no following span → extends to volume_end.
        lemma = {
            "proof_read": 2,
            "chapters": [{"start": 2, "author": "Abert"}],
        }
        result = _build_row_articles([lemma], 1, 5, self.authors, "I,1")
        compare([[], [COLOR_YELLOW], [COLOR_YELLOW], [COLOR_YELLOW], [COLOR_YELLOW]], result)

    def test_open_ended_span_clipped_to_next_span_start(self):
        first = {"proof_read": 2, "chapters": [{"start": 1, "author": "Abert"}]}
        second = {"proof_read": 3, "chapters": [{"start": 4, "end": 4, "author": "Abert"}]}
        result = _build_row_articles([first, second], 1, 5, self.authors, "I,1")
        compare(
            [[COLOR_YELLOW], [COLOR_YELLOW], [COLOR_YELLOW], [COLOR_GREEN], []],
            result,
        )

    def test_open_ended_span_does_not_swallow_co_starting_long_span(self):
        # Regression: an open-ended lemma at column 5 must not be extended through a
        # closed span that begins on the same column.
        open_ended = {"proof_read": 2, "chapters": [{"start": 5, "author": "Abert"}]}
        long_span = {
            "proof_read": 3,
            "chapters": [{"start": 5, "end": 9, "author": "Abert"}],
        }
        result = _build_row_articles([open_ended, long_span], 1, 10, self.authors, "I,1")
        compare(
            [[], [], [], [],
             [COLOR_YELLOW, COLOR_GREEN], [COLOR_GREEN], [COLOR_GREEN], [COLOR_GREEN], [COLOR_GREEN],
             []],
            result,
        )

    def test_open_ended_span_blocked_by_long_closed_starting_earlier_in_sort(self):
        # Regression for S XI: when a long closed span shares the open-ended span's
        # start column AND was input first (so it sorts before the open span), the
        # open span must still be clamped to its own start — not extended across the
        # closed article's body to the next sorted neighbour.
        long_span = {
            "proof_read": 3,
            "chapters": [{"start": 5, "end": 9, "author": "Abert"}],
        }
        open_ended = {"proof_read": 2, "chapters": [{"start": 5, "author": "Abert"}]}
        far = {"proof_read": 3, "chapters": [{"start": 12, "end": 12, "author": "Abert"}]}
        # Order matters: long_span first ensures it sorts before open_ended at col 5.
        result = _build_row_articles([long_span, open_ended, far], 1, 13, self.authors, "I,1")
        expected = [
            [], [], [], [],
            [COLOR_GREEN, COLOR_YELLOW],     # col 5 — both articles begin here
            [COLOR_GREEN], [COLOR_GREEN], [COLOR_GREEN], [COLOR_GREEN],  # cols 6–9 — long span only
            [], [],                           # cols 10–11 — gap
            [COLOR_GREEN],                    # col 12 — far span
            [],                               # col 13
        ]
        compare(expected, result)

    def test_overlapping_spans_stack_colors(self):
        first = {"proof_read": 3, "chapters": [{"start": 1, "end": 3, "author": "Abert"}]}
        second = {"proof_read": 2, "chapters": [{"start": 2, "end": 4, "author": "Abert"}]}
        result = _build_row_articles([first, second], 1, 4, self.authors, "I,1")
        compare(
            [[COLOR_GREEN], [COLOR_GREEN, COLOR_YELLOW], [COLOR_GREEN, COLOR_YELLOW], [COLOR_YELLOW]],
            result,
        )

    def test_columns_outside_volume_window_are_clipped(self):
        # Span 1..10 but window only covers columns 3..5.
        lemma = {"proof_read": 3, "chapters": [{"start": 1, "end": 10, "author": "Abert"}]}
        result = _build_row_articles([lemma], 3, 3, self.authors, "I,1")
        compare([[COLOR_GREEN], [COLOR_GREEN], [COLOR_GREEN]], result)

    def test_multiple_chapters_use_widest_extent(self):
        lemma = {
            "proof_read": 3,
            "chapters": [
                {"start": 4, "end": 4, "author": "Abert"},
                {"start": 4, "end": 5, "author": "Abert"},
            ],
        }
        result = _build_row_articles([lemma], 1, 6, self.authors, "I,1")
        compare([[], [], [], [COLOR_GREEN], [COLOR_GREEN], []], result)


class TestLoadFont:
    def test_returns_a_font_object(self):
        font = _load_font()
        assert font is not None

    def test_falls_back_to_default_when_truetype_unavailable(self):
        with mock.patch(
            "service.ws_re.register.picture.ImageFont.truetype",
            side_effect=OSError,
        ):
            font = _load_font()
        compare(True, isinstance(font, (ImageFont.ImageFont, ImageFont.FreeTypeFont)))


class TestCreatePicture(BaseTestRegister):
    def setUp(self):
        copy_tst_data("I_1_alpha", "I_1")

    def test_creates_png_with_expected_dimensions(self):
        volume = Volume(name="I,1", year=1893, data_item="Q1", start_column="1", end_column="10")
        with mock.patch("service.ws_re.register.picture.Volumes") as volumes_mock:
            volumes_mock.return_value.all_volumes = [volume]
            with tempfile.TemporaryDirectory() as tmp_dir:
                out_path = Path(tmp_dir).joinpath("out.png")
                create_picture(out_path)
                compare(True, out_path.exists())
                with Image.open(out_path) as image:
                    compare("PNG", image.format)
                    compare((LABEL_WIDTH + 10, HEADER_HEIGHT + LINE_HEIGHT), image.size)

    def test_skips_volumes_without_columns(self):
        # The volume without columns is skipped; only I,1 contributes a row.
        volume_with_columns = Volume(
            name="I,1", year=1893, data_item="Q1", start_column="1", end_column="5"
        )
        volume_no_columns = Volume(name="R", year=1980, data_item="Q9")
        with mock.patch("service.ws_re.register.picture.Volumes") as volumes_mock:
            volumes_mock.return_value.all_volumes = [volume_with_columns, volume_no_columns]
            with tempfile.TemporaryDirectory() as tmp_dir:
                out_path = Path(tmp_dir).joinpath("out.png")
                create_picture(out_path)
                with Image.open(out_path) as image:
                    compare((LABEL_WIDTH + 5, HEADER_HEIGHT + LINE_HEIGHT), image.size)

    def test_skips_volumes_without_json_file(self):
        present = Volume(
            name="I,1", year=1893, data_item="Q1", start_column="1", end_column="5"
        )
        missing = Volume(
            name="II,1", year=1896, data_item="Q2", start_column="1", end_column="5"
        )
        with mock.patch("service.ws_re.register.picture.Volumes") as volumes_mock:
            volumes_mock.return_value.all_volumes = [present, missing]
            with tempfile.TemporaryDirectory() as tmp_dir:
                out_path = Path(tmp_dir).joinpath("out.png")
                create_picture(out_path)
                with Image.open(out_path) as image:
                    # Only one row (the present volume) is rendered.
                    compare(HEADER_HEIGHT + LINE_HEIGHT, image.size[1])

    def test_renders_label_and_bar_pixels(self):
        volume = Volume(
            name="I,1", year=1893, data_item="Q1", start_column="1", end_column="6"
        )
        # Single PD lemma with proof_read=3 → green bar across the entire volume span.
        lemmas = [
            {
                "lemma": "Solo",
                "proof_read": 3,
                "no_creative_height": True,
                "chapters": [{"start": 1, "end": 6, "author": "Abert"}],
            }
        ]
        json_file = Path(__file__).parent.joinpath("mock_data", "I_1.json")
        with open(json_file, "w", encoding="utf-8") as fp:
            json.dump(lemmas, fp)
        with mock.patch("service.ws_re.register.picture.Volumes") as volumes_mock:
            volumes_mock.return_value.all_volumes = [volume]
            with tempfile.TemporaryDirectory() as tmp_dir:
                out_path = Path(tmp_dir).joinpath("out.png")
                create_picture(out_path)
                with Image.open(out_path) as image:
                    pixels = image.load()
                    # Bar pixels are green inside the span.
                    compare(COLOR_GREEN, pixels[LABEL_WIDTH, HEADER_HEIGHT])
                    compare(COLOR_GREEN, pixels[LABEL_WIDTH + 5, HEADER_HEIGHT])

    def test_gridline_does_not_overwrite_marked_column_data(self):
        # Col 50 is the first marked column. Give it its own (yellow) lemma so
        # we can prove the gridline gap doesn't replace its data.
        volume = Volume(
            name="I,1", year=1893, data_item="Q1", start_column="1", end_column="55"
        )
        lemmas = [
            {
                "lemma": "Before",
                "proof_read": 3,
                "no_creative_height": True,
                "chapters": [{"start": 1, "end": 49, "author": "Abert"}],
            },
            {
                "lemma": "Marked",
                "proof_read": 2,
                "no_creative_height": True,
                "chapters": [{"start": 50, "end": 50, "author": "Abert"}],
            },
            {
                "lemma": "After",
                "proof_read": 3,
                "no_creative_height": True,
                "chapters": [{"start": 51, "end": 55, "author": "Abert"}],
            },
        ]
        json_file = Path(__file__).parent.joinpath("mock_data", "I_1.json")
        with open(json_file, "w", encoding="utf-8") as fp:
            json.dump(lemmas, fp)
        with mock.patch("service.ws_re.register.picture.Volumes") as volumes_mock:
            volumes_mock.return_value.all_volumes = [volume]
            with tempfile.TemporaryDirectory() as tmp_dir:
                out_path = Path(tmp_dir).joinpath("out.png")
                create_picture(out_path)
                with Image.open(out_path) as image:
                    pixels = image.load()
                    bar_y = HEADER_HEIGHT + 1
                    # Col 49 (offset 48) green, gridline gap (offset 49) white,
                    # col 50 (offset 50) yellow — preserved! — col 51 (offset 51) green.
                    compare(COLOR_GREEN, pixels[LABEL_WIDTH + 48, bar_y])
                    compare(COLOR_WHITE, pixels[LABEL_WIDTH + 49, bar_y])
                    compare(COLOR_YELLOW, pixels[LABEL_WIDTH + 50, bar_y])
                    compare(COLOR_GREEN, pixels[LABEL_WIDTH + 51, bar_y])

    def test_each_row_has_its_own_header_and_gridline(self):
        # Two volumes with different start columns. Each row gets its own header
        # placed directly above its bar, and gridlines align with that volume's
        # actual column numbers.
        volume_a = Volume(
            name="I,1", year=1893, data_item="Q1", start_column="1", end_column="250"
        )
        volume_b = Volume(
            name="I,2", year=1894, data_item="Q2", start_column="1439", end_column="1700"
        )
        lemmas_a = [{
            "lemma": "A", "proof_read": 3, "no_creative_height": True,
            "chapters": [{"start": 1, "end": 250, "author": "Abert"}],
        }]
        lemmas_b = [{
            "lemma": "B", "proof_read": 3, "no_creative_height": True,
            "chapters": [{"start": 1439, "end": 1700, "author": "Abert"}],
        }]
        mock_dir = Path(__file__).parent.joinpath("mock_data")
        with open(mock_dir.joinpath("I_1.json"), "w", encoding="utf-8") as fp:
            json.dump(lemmas_a, fp)
        with open(mock_dir.joinpath("I_2.json"), "w", encoding="utf-8") as fp:
            json.dump(lemmas_b, fp)
        with mock.patch("service.ws_re.register.picture.Volumes") as volumes_mock:
            volumes_mock.return_value.all_volumes = [volume_a, volume_b]
            with tempfile.TemporaryDirectory() as tmp_dir:
                out_path = Path(tmp_dir).joinpath("out.png")
                create_picture(out_path)
                with Image.open(out_path) as image:
                    pixels = image.load()
                    row_block = HEADER_HEIGHT + LINE_HEIGHT
                    bar_a_y = HEADER_HEIGHT + 1
                    bar_b_y = row_block + HEADER_HEIGHT + 1
                    # The gridline gap is inserted *before* each marked column
                    # so the column's data is not overwritten.
                    # Volume I,1 (start=1): gridline gaps before cols 50, 100, 150
                    # → offsets 49, 100, 151. Each marked column's data sits one
                    # pixel after its gap (col 50 at 50, col 100 at 101, …).
                    compare(COLOR_WHITE, pixels[LABEL_WIDTH + 49, bar_a_y])
                    compare(COLOR_WHITE, pixels[LABEL_WIDTH + 100, bar_a_y])
                    compare(COLOR_WHITE, pixels[LABEL_WIDTH + 151, bar_a_y])
                    # Marked-column data is preserved (no overlap).
                    compare(COLOR_GREEN, pixels[LABEL_WIDTH + 50, bar_a_y])
                    compare(COLOR_GREEN, pixels[LABEL_WIDTH + 101, bar_a_y])
                    # Volume I,2 (start=1439): first marked column is 1450, at
                    # col_idx 11. Gap goes before it → offset 11. Next marked
                    # column 1500 sits 50 cols later, with one gap already
                    # inserted, so its gap is at offset 62.
                    compare(COLOR_WHITE, pixels[LABEL_WIDTH + 11, bar_b_y])
                    compare(COLOR_WHITE, pixels[LABEL_WIDTH + 62, bar_b_y])
                    # Col 1450 data preserved at offset 12, col 1500 at offset 63.
                    compare(COLOR_GREEN, pixels[LABEL_WIDTH + 12, bar_b_y])
                    compare(COLOR_GREEN, pixels[LABEL_WIDTH + 63, bar_b_y])

    def test_draws_white_gridline_every_50_columns(self):
        # Bar wide enough to contain several gridlines (at columns 50, 100, …).
        volume = Volume(
            name="I,1", year=1893, data_item="Q1", start_column="1", end_column="250"
        )
        # Single green span covering the full bar — gridline pixels must overwrite it.
        lemmas = [
            {
                "lemma": "Solo",
                "proof_read": 3,
                "no_creative_height": True,
                "chapters": [{"start": 1, "end": 250, "author": "Abert"}],
            }
        ]
        json_file = Path(__file__).parent.joinpath("mock_data", "I_1.json")
        with open(json_file, "w", encoding="utf-8") as fp:
            json.dump(lemmas, fp)
        with mock.patch("service.ws_re.register.picture.Volumes") as volumes_mock:
            volumes_mock.return_value.all_volumes = [volume]
            with tempfile.TemporaryDirectory() as tmp_dir:
                out_path = Path(tmp_dir).joinpath("out.png")
                create_picture(out_path)
                with Image.open(out_path) as image:
                    pixels = image.load()
                    bar_y = HEADER_HEIGHT + 1
                    # Gridline gaps before cols 50, 100, 150 → offsets 49, 100, 151.
                    compare(COLOR_WHITE, pixels[LABEL_WIDTH + 49, bar_y])
                    compare(COLOR_WHITE, pixels[LABEL_WIDTH + 100, bar_y])
                    compare(COLOR_WHITE, pixels[LABEL_WIDTH + 151, bar_y])
                    # Marked column data is preserved on the right side of the
                    # gap (col 50 at offset 50, col 100 at offset 101).
                    compare(COLOR_GREEN, pixels[LABEL_WIDTH + 48, bar_y])
                    compare(COLOR_GREEN, pixels[LABEL_WIDTH + 50, bar_y])
                    compare(COLOR_GREEN, pixels[LABEL_WIDTH + 101, bar_y])
