# pylint: disable=protected-access
from datetime import date
from unittest import mock

from testfixtures import compare

from service.ws_re.register.statistic.chart import (
    ARTICLE_CHART,
    ARTICLE_DETAIL_CHART,
    CHART_PALETTE,
    COLUMN_CHART,
    COLUMN_DETAIL_CHART,
    WEEKLY,
    HistoryCharts,
    _area_color,
    _article_weights,
    _column_weights,
    _quarter_ends,
    _sundays,
)
from service.ws_re.register.test_base import BaseTestRegister, copy_tst_data
from service.ws_re.volumes import Volume

LEMMAS = [
    # created as unkorrigiert, later fertig (skipped korrigiert)
    {"lemma": "a", "history": {"1": "070201", "3": "070815"}},
    # created after the first quarter
    {"lemma": "b", "history": {"0": "070401"}},
    # dropped back: the higher states were deleted, korrigiert carries the date of the drop
    {"lemma": "c", "history": {"0": "070101", "2": "071001"}},
    # never created
    {"lemma": "d"},
]
# volume without known columns
VOLUMES = [(Volume(name="R", year=1980, data_item="Q9"), LEMMAS)]
# columns 1–6: a a [a b e] c c d
COLUMN_VOLUMES = [
    (
        Volume(name="I,1", year=1893, data_item="Q1", start_column="1", end_column="6"),
        [
            {"lemma": "a", "history": {"1": "070201", "3": "070815"}, "chapters": [{"start": 1, "end": 3}]},
            {"lemma": "b", "history": {"0": "070401"}, "chapters": [{"start": 3, "end": 3}]},
            {"lemma": "e", "history": {"2": "070101"}, "chapters": [{"start": 3, "end": 3}]},
            {"lemma": "c", "history": {"0": "070101", "2": "071001"}, "chapters": [{"start": 4, "end": 5}]},
            {"lemma": "d", "chapters": [{"start": 6, "end": 6}]},
        ],
    )
]
COLUMNS = ["erfasst", "korrigiert", "unkorrigiert", "fertig"]


class TestHistoryChart(BaseTestRegister):
    def test_quarter_ends(self):
        compare(
            [
                date(2007, 3, 31),
                date(2007, 6, 30),
                date(2007, 9, 30),
                date(2007, 12, 31),
                date(2008, 3, 31),
                date(2008, 5, 1),
            ],
            _quarter_ends(date(2008, 5, 1)),
        )

    def test_quarter_ends_today_is_quarter_end(self):
        compare([date(2007, 3, 31), date(2007, 6, 30)], _quarter_ends(date(2007, 6, 30)))

    def test_sundays(self):
        # 2026-01-04 is the first sunday of 2026
        compare([date(2026, 1, 4), date(2026, 1, 11), date(2026, 1, 18)], _sundays(date(2026, 1, 24)))

    def test_sundays_today_is_sunday(self):
        compare([date(2026, 1, 4), date(2026, 1, 11)], _sundays(date(2026, 1, 11)))

    def test_sundays_year_starts_with_sunday(self):
        # 2023-01-01 is a sunday
        compare([date(2023, 1, 1)], _sundays(date(2023, 1, 1)))

    def test_sundays_before_the_first_sunday(self):
        compare([date(2026, 1, 2)], _sundays(date(2026, 1, 2)))

    def test_build_rows_weekly(self):
        chart = ARTICLE_CHART.with_period("detail", WEEKLY)
        compare(
            [["2007-01-07", 1, 0, 0, 0], ["2007-01-14", 1, 0, 0, 0]],
            chart.build_rows(VOLUMES, date(2007, 1, 20), COLUMNS),
        )

    def test_detail_charts(self):
        compare("Pauly-Wissowa/stats/articles detail", ARTICLE_DETAIL_CHART.name)
        compare("Pauly-Wissowa/stats/columns detail", COLUMN_DETAIL_CHART.name)
        definition = COLUMN_DETAIL_CHART.create_definition()
        compare("Pauly-Wissowa/stats/columns detail.tab", definition["source"])
        compare("Paulys Realencyclopädie: Spalten nach Bearbeitungsstand im laufenden Jahr", definition["title"]["de"])
        compare(
            "Paulys Realencyclopädie: columns by proofreading status in the current year", definition["title"]["en"]
        )
        data = COLUMN_DETAIL_CHART.create_data(COLUMN_VOLUMES, date(2007, 1, 7))
        compare(True, data["description"]["de"].endswith("jeweils sonntags im laufenden Jahr"))
        compare(True, data["description"]["en"].endswith("every Sunday of the current year"))

    def test_article_weights(self):
        compare([(lemma, 1.0) for lemma in LEMMAS], _article_weights(VOLUMES))

    def test_column_weights(self):
        weights = {lemma["lemma"]: round(weight, 3) for lemma, weight in _column_weights(COLUMN_VOLUMES)}
        # column 3 is shared by a, b and e
        compare({"a": 2.333, "b": 0.333, "e": 0.333, "c": 2.0, "d": 1.0}, weights)

    def test_column_weights_skips_volumes_without_columns(self):
        compare([], _column_weights(VOLUMES))

    def test_column_weights_skips_lemmas_outside_of_the_volume(self):
        volume = Volume(name="I,1", year=1893, data_item="Q1", start_column="1", end_column="2")
        lemmas = [{"lemma": "a", "chapters": [{"start": 1, "end": 2}]}, {"lemma": "b", "chapters": [{"start": 5}]}]
        compare([(lemmas[0], 2.0)], _column_weights([(volume, lemmas)]))

    def test_build_rows_articles(self):
        compare(
            [
                ["2007-03-31", 1, 0, 1, 0],
                ["2007-06-30", 2, 0, 1, 0],
                ["2007-09-30", 2, 0, 0, 1],
                ["2007-11-01", 1, 1, 0, 1],
            ],
            ARTICLE_CHART.build_rows(VOLUMES, date(2007, 11, 1), COLUMNS),
        )

    def test_build_rows_columns(self):
        compare(
            [
                ["2007-03-31", 2, 0, 2, 0],
                ["2007-06-30", 2, 0, 2, 0],
                ["2007-09-30", 2, 0, 0, 2],
                ["2007-11-01", 0, 2, 0, 2],
            ],
            COLUMN_CHART.build_rows(COLUMN_VOLUMES, date(2007, 11, 1), COLUMNS),
        )

    def test_build_rows_column_order(self):
        compare(
            [["2007-02-01", 0, 1, 1]],
            ARTICLE_CHART.build_rows(VOLUMES, date(2007, 2, 1), ["fertig", "erfasst", "unkorrigiert"]),
        )

    def test_create_data(self):
        volumes = [(Volume(name="R", year=1980, data_item="Q9"), [{"lemma": "a", "history": {"3": "070101"}}])]
        data = ARTICLE_CHART.create_data(volumes, date(2007, 2, 1))
        compare("CC0-1.0", data["license"])
        # order of the palette of the chart renderer: blue, yellow, red, teal
        compare(
            ["datum", "erfasst", "korrigiert", "unkorrigiert", "fertig"],
            [field["name"] for field in data["schema"]["fields"]],
        )
        compare(
            ["Datum", "Erfasst", "Korrigiert", "Unkorrigiert", "Fertig"],
            [field["title"]["de"] for field in data["schema"]["fields"]],
        )
        compare(
            True, "[[:s:de:Paulys Realencyclopädie der classischen Altertumswissenschaft/Statistik]]" in data["sources"]
        )
        compare(True, data["description"]["de"].startswith("Anzahl der Artikel der Paulys"))
        compare([["2007-02-01", 0, 0, 0, 1]], data["data"])

    def test_create_data_columns(self):
        data = COLUMN_CHART.create_data([], date(2007, 2, 1))
        compare(True, data["description"]["de"].startswith("Anzahl der Spalten der Artikel der Paulys"))
        compare(True, data["description"]["en"].startswith("Number of columns of the articles of Paulys"))

    def test_create_definition(self):
        definition = ARTICLE_CHART.create_definition()
        compare("area", definition["type"])
        compare("CC0-1.0", definition["license"])
        compare("Pauly-Wissowa/stats/articles.tab", definition["source"])
        compare("Paulys Realencyclopädie: Artikel nach Bearbeitungsstand", definition["title"]["de"])
        compare("Paulys Realencyclopädie: articles by proofreading status", definition["title"]["en"])
        compare({"title": {"de": "Artikel", "en": "Articles"}}, definition["yAxis"])

    def test_create_definition_columns(self):
        definition = COLUMN_CHART.create_definition()
        compare("Pauly-Wissowa/stats/columns.tab", definition["source"])
        compare("Paulys Realencyclopädie: Spalten nach Bearbeitungsstand", definition["title"]["de"])
        compare({"title": {"de": "Spalten", "en": "Columns"}}, definition["yAxis"])


class TestHistoryCharts(BaseTestRegister):
    def test_area_color(self):
        # 70 % of the color on white
        compare("#81a0e2", _area_color("#4b77d6"))
        compare("#ffffff", _area_color("#ffffff"))

    def test_create_table(self):
        today = date(2007, 6, 30)
        datasets = [
            (ARTICLE_CHART, ARTICLE_CHART.create_data(VOLUMES, today)),
            (COLUMN_CHART, COLUMN_CHART.create_data(COLUMN_VOLUMES, today)),
        ]
        blue, yellow, red, teal = (f'style="background:{color}" | ' for color in CHART_PALETTE[:4])
        light_blue, light_yellow, light_red, light_teal = (
            f'style="background:{_area_color(color)}" | ' for color in CHART_PALETTE[:4]
        )
        # unkorrigiert before korrigiert, every column keeps the color of its series
        header = f"! {blue}Erfasst !! {red}Unkorrigiert !! {yellow}Korrigiert !! {teal}Fertig"

        def cells(erfasst: int, unkorrigiert: int, korrigiert: int, fertig: int) -> str:
            return (
                f"{light_blue}{{{{formatnum:{erfasst}}}}} || {light_red}{{{{formatnum:{unkorrigiert}}}}} || "
                f"{light_yellow}{{{{formatnum:{korrigiert}}}}} || {light_teal}{{{{formatnum:{fertig}}}}}"
            )

        compare(
            '{| class="wikitable" style="text-align:right"\n'
            '! rowspan="2" | Datum\n'
            '! colspan="4" | Artikel\n'
            '! colspan="4" | Spalten\n'
            "|-\n"
            f"{header} !! {header[2:]}\n"
            "|-\n"
            f"| 2007-06-30 || {cells(2, 1, 0, 0)} || {cells(2, 2, 0, 0)}\n"
            "|-\n"
            f"| 2007-03-31 || {cells(1, 1, 0, 0)} || {cells(2, 2, 0, 0)}\n"
            "|}",
            HistoryCharts.create_table(datasets),
        )

    def test_create_page_text(self):
        text = HistoryCharts.create_page_text("TABLE", "DETAIL_TABLE")
        charts = [
            "{{#chart:Pauly-Wissowa/stats/articles.chart}}",
            "{{#chart:Pauly-Wissowa/stats/columns.chart}}",
            "[[Datei:Pauly-Wissowa stats overview.png|",
            "=== Daten ===\nTABLE\n",
            "== Bearbeitungsstand im laufenden Jahr ==",
            "{{#chart:Pauly-Wissowa/stats/articles detail.chart}}",
            "{{#chart:Pauly-Wissowa/stats/columns detail.chart}}",
        ]
        compare(sorted(text.index(part) for part in charts), [text.index(part) for part in charts])
        compare(True, text.endswith("=== Daten ===\nDETAIL_TABLE\n"))

    def test_update(self):
        copy_tst_data("I_1_alpha", "I_1")
        volume = Volume(name="I,1", year=1893, data_item="Q1", start_column="1", end_column="10")
        wiki, commons = mock.Mock(), mock.Mock()
        with (
            mock.patch("service.ws_re.register.statistic.base.Volumes") as volumes_mock,
            mock.patch("service.ws_re.register.statistic.chart.Page") as page_mock,
            mock.patch("service.ws_re.register.statistic.chart.save_json_page") as save_json_mock,
            mock.patch("service.ws_re.register.statistic.chart.save_page") as save_mock,
        ):
            volumes_mock.return_value.all_volumes = [volume]
            HistoryCharts(wiki, commons, mock.Mock()).update(date(2007, 2, 1))
        compare(
            [
                mock.call(commons, "Data:Pauly-Wissowa/stats/articles.tab"),
                mock.call(commons, "Data:Pauly-Wissowa/stats/articles.chart"),
                mock.call(commons, "Data:Pauly-Wissowa/stats/columns.tab"),
                mock.call(commons, "Data:Pauly-Wissowa/stats/columns.chart"),
                mock.call(commons, "Data:Pauly-Wissowa/stats/articles detail.tab"),
                mock.call(commons, "Data:Pauly-Wissowa/stats/articles detail.chart"),
                mock.call(commons, "Data:Pauly-Wissowa/stats/columns detail.tab"),
                mock.call(commons, "Data:Pauly-Wissowa/stats/columns detail.chart"),
                mock.call(wiki, "Paulys Realencyclopädie der classischen Altertumswissenschaft/Statistik"),
            ],
            page_mock.call_args_list,
        )
        saved = [call.args[1] for call in save_json_mock.call_args_list]
        compare(8, len(saved))
        compare(["2007-02-01"], [row[0] for row in saved[0]["data"]])
        compare(["2007-01-07", "2007-01-14", "2007-01-21", "2007-01-28"], [row[0] for row in saved[4]["data"]])
        compare(ARTICLE_CHART.create_definition(), saved[1])
        compare(COLUMN_CHART.create_definition(), saved[3])
        compare(ARTICLE_DETAIL_CHART.create_definition(), saved[5])
        compare(COLUMN_DETAIL_CHART.create_definition(), saved[7])
        compare(
            HistoryCharts.create_page_text(
                HistoryCharts.create_table([(ARTICLE_CHART, saved[0]), (COLUMN_CHART, saved[2])]),
                HistoryCharts.create_table([(ARTICLE_DETAIL_CHART, saved[4]), (COLUMN_DETAIL_CHART, saved[6])]),
            ),
            save_mock.call_args.args[1],
        )
