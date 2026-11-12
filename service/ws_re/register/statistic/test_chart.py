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
    QUARTERLY,
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
        definition = COLUMN_DETAIL_CHART.of_year(2007).create_definition()
        compare("Pauly-Wissowa/stats/columns detail 2007.tab", definition["source"])
        compare("Spalten nach Bearbeitungsstand im Jahr", definition["title"]["de"])
        compare("Columns by proofreading status in the year", definition["title"]["en"])
        data = COLUMN_DETAIL_CHART.of_year(2007).create_data(COLUMN_VOLUMES, date(2007, 1, 7))
        compare(True, data["description"]["de"].endswith("jeweils sonntags im Jahr 2007"))
        compare(True, data["description"]["en"].endswith("every Sunday of 2007"))

    def test_of_year(self):
        chart = ARTICLE_CHART.of_year(2020)
        compare("Pauly-Wissowa/stats/articles 2020", chart.tab_name)
        compare("Pauly-Wissowa/stats/articles.chart|data=Pauly-Wissowa/stats/articles 2020.tab", chart.embedding)
        # the quarterly data covers all years up to the year
        compare(QUARTERLY, chart.period)

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
        definition = ARTICLE_CHART.of_year(2026).create_definition()
        compare("area", definition["type"])
        compare("CC0-1.0", definition["license"])
        compare("Pauly-Wissowa/stats/articles 2026.tab", definition["source"])
        compare("Artikel nach Bearbeitungsstand", definition["title"]["de"])
        compare("Articles by proofreading status", definition["title"]["en"])
        compare({"title": {"de": "Artikel", "en": "Articles"}}, definition["yAxis"])

    def test_create_definition_columns(self):
        definition = COLUMN_CHART.of_year(2026).create_definition()
        compare("Pauly-Wissowa/stats/columns 2026.tab", definition["source"])
        compare("Spalten nach Bearbeitungsstand", definition["title"]["de"])
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
        text = HistoryCharts.create_page_text("TABLE", "DETAIL_TABLE", 2026)
        # The detail charts stand side by side in a table. Headings in table cells are moved out of the table by
        # MediaWiki, so header cells name the charts. A chart in a mw-collapsible block stays blank (ECharts is
        # initialized twice), so only the data tables collapse. Their heading stays outside of the collapsible block,
        # otherwise it collapses with the content.
        side_by_side = (
            '! style="width:50%; text-align:left; font-size:1.2em" | Artikel\n'
            '! style="width:50%; text-align:left; font-size:1.2em" | Spalten\n'
            "|-\n"
            '| style="vertical-align:top" |\n{{{{#chart:{0}.chart|data={0} 2026.tab}}}}\n'
            '| style="vertical-align:top" |\n{{{{#chart:{1}.chart|data={1} 2026.tab}}}}\n'
            "|}}\n"
        )
        collapsed = '=== {} ===\n<div class="mw-collapsible mw-collapsed">\n{}\n</div>\n'
        stats = "Pauly-Wissowa/stats"
        parts = [
            '| style="width:50%" | [[Datei:Pauly-Wissowa stats overview 2026.png|',
            "== Fortschritt ==",
            f"=== Artikel ===\n{{{{#chart:{stats}/articles.chart|data={stats}/articles 2026.tab}}}}\n\n"
            + f"=== Spalten ===\n{{{{#chart:{stats}/columns.chart|data={stats}/columns 2026.tab}}}}\n",
            collapsed.format("Daten", "TABLE"),
            "== Fortschritt 2026 ==",
            side_by_side.format(f"{stats}/articles detail", f"{stats}/columns detail"),
        ]
        compare(sorted(text.index(part) for part in parts), [text.index(part) for part in parts])
        compare(True, text.endswith(collapsed.format("Daten", "DETAIL_TABLE")))
        compare(False, "Bearbeitungsstand im laufenden Jahr" in text)

    def test_update(self):
        copy_tst_data("I_1_alpha", "I_1")
        volume = Volume(name="I,1", year=1893, data_item="Q1", start_column="1", end_column="10")
        wiki, commons = mock.Mock(), mock.Mock()
        with (
            mock.patch("service.ws_re.register.statistic.base.Volumes") as volumes_mock,
            mock.patch("service.ws_re.register.statistic.chart.Page") as page_mock,
            mock.patch("service.ws_re.register.statistic.chart.save_json_page") as save_json_mock,
            mock.patch("service.ws_re.register.statistic.chart.save_page") as save_mock,
            # 2009 isn't past yet
            mock.patch("service.ws_re.register.statistic.chart.PAST_YEARS", (2007, 2009)),
            mock.patch("service.ws_re.register.statistic.chart.STATISTIC_VOLUMES", ("I,1",)),
        ):
            volumes_mock.return_value.all_volumes = [volume]
            HistoryCharts(wiki, commons, mock.Mock()).update(date(2008, 2, 1))
        stats = "Data:Pauly-Wissowa/stats"
        statistic_page = "Paulys Realencyclopädie der classischen Altertumswissenschaft/Statistik"
        compare(
            [
                mock.call(wiki, "Vorlage:RE Statistik Navigation"),
                # the past year has only its own data, the chart definitions are shared
                *(
                    mock.call(commons, f"{stats}/{name} 2007.tab")
                    for name in ("articles", "columns", "articles detail", "columns detail")
                ),
                mock.call(wiki, f"{statistic_page}/2007"),
                # the current year has its own data and maintains the chart definitions, they link its data
                *(
                    mock.call(commons, path)
                    for name in ("articles", "columns", "articles detail", "columns detail")
                    for path in (f"{stats}/{name} 2008.tab", f"{stats}/{name}.chart")
                ),
                mock.call(wiki, f"{statistic_page}/2008"),
                mock.call(wiki, statistic_page),
                # the volume has only its own data
                *(
                    mock.call(commons, f"{stats}/{name} I,1.tab")
                    for name in ("articles", "columns", "articles detail", "columns detail")
                ),
                mock.call(wiki, f"{statistic_page}/I,1"),
            ],
            page_mock.call_args_list,
        )
        saved = [call.args[1] for call in save_json_mock.call_args_list]
        compare(16, len(saved))
        # the volume up to today, its weekly data covers the current year
        compare(saved[4]["data"], saved[12]["data"])
        compare(saved[8]["data"], saved[14]["data"])
        compare(True, saved[12]["description"]["de"].startswith("Anzahl der Artikel des Bandes I,1 der Paulys"))
        compare(
            HistoryCharts.create_page_text(
                HistoryCharts.create_table([(ARTICLE_CHART, saved[12]), (COLUMN_CHART, saved[13])]),
                HistoryCharts.create_table([(ARTICLE_DETAIL_CHART, saved[14]), (COLUMN_DETAIL_CHART, saved[15])]),
                2008,
                "I,1",
            ),
            save_mock.call_args_list[4].args[1],
        )
        # the past year ends with its last day
        compare(["2007-03-31", "2007-06-30", "2007-09-30", "2007-12-31"], [row[0] for row in saved[0]["data"]])
        compare(52, len(saved[2]["data"]))
        compare("2007-12-30", saved[2]["data"][-1][0])
        compare(True, saved[2]["description"]["de"].endswith("jeweils sonntags im Jahr 2007"))
        compare(
            HistoryCharts.create_page_text(
                HistoryCharts.create_table([(ARTICLE_CHART, saved[0]), (COLUMN_CHART, saved[1])]),
                HistoryCharts.create_table([(ARTICLE_DETAIL_CHART, saved[2]), (COLUMN_DETAIL_CHART, saved[3])]),
                2007,
            ),
            save_mock.call_args_list[1].args[1],
        )
        # the current year ends today
        compare(
            ["2007-03-31", "2007-06-30", "2007-09-30", "2007-12-31", "2008-02-01"], [row[0] for row in saved[4]["data"]]
        )
        compare(["2008-01-06", "2008-01-13", "2008-01-20", "2008-01-27"], [row[0] for row in saved[8]["data"]])
        compare(ARTICLE_CHART.of_year(2008).create_definition(), saved[5])
        compare(COLUMN_CHART.of_year(2008).create_definition(), saved[7])
        compare(ARTICLE_DETAIL_CHART.of_year(2008).create_definition(), saved[9])
        compare(COLUMN_DETAIL_CHART.of_year(2008).create_definition(), saved[11])
        compare(
            HistoryCharts.create_page_text(
                HistoryCharts.create_table([(ARTICLE_CHART, saved[4]), (COLUMN_CHART, saved[6])]),
                HistoryCharts.create_table([(ARTICLE_DETAIL_CHART, saved[8]), (COLUMN_DETAIL_CHART, saved[10])]),
                2008,
            ),
            save_mock.call_args_list[2].args[1],
        )
        compare(HistoryCharts.create_navigation(["I,1"], 2008), save_mock.call_args_list[0].args[1])
        compare(f"#WEITERLEITUNG [[{statistic_page}/2008]]", save_mock.call_args_list[3].args[1])

    def test_page_text_of_a_volume(self):
        text = HistoryCharts.create_page_text("TABLE", "DETAIL_TABLE", 2026, "S III")
        for part in (
            "[[Datei:Pauly-Wissowa stats overview S III.png|",
            "{{#chart:Pauly-Wissowa/stats/articles.chart|data=Pauly-Wissowa/stats/articles S III.tab}}",
            "{{#chart:Pauly-Wissowa/stats/columns.chart|data=Pauly-Wissowa/stats/columns S III.tab}}",
            "== Fortschritt 2026 ==",
            "{{#chart:Pauly-Wissowa/stats/articles detail.chart|data=Pauly-Wissowa/stats/articles detail S III.tab}}",
            "{{#chart:Pauly-Wissowa/stats/columns detail.chart|data=Pauly-Wissowa/stats/columns detail S III.tab}}",
        ):
            compare(True, part in text)

    def test_page_text_of_a_past_year(self):
        text = HistoryCharts.create_page_text("TABLE", "DETAIL_TABLE", 2020)
        for part in (
            "[[Datei:Pauly-Wissowa stats overview 2020.png|",
            # the shared chart definitions with the data of the year
            "{{#chart:Pauly-Wissowa/stats/articles.chart|data=Pauly-Wissowa/stats/articles 2020.tab}}",
            "{{#chart:Pauly-Wissowa/stats/columns.chart|data=Pauly-Wissowa/stats/columns 2020.tab}}",
            "== Fortschritt 2020 ==",
            "{{#chart:Pauly-Wissowa/stats/articles detail.chart|data=Pauly-Wissowa/stats/articles detail 2020.tab}}",
            "{{#chart:Pauly-Wissowa/stats/columns detail.chart|data=Pauly-Wissowa/stats/columns detail 2020.tab}}",
        ):
            compare(True, part in text)

    def test_create_navigation(self):
        text = HistoryCharts.create_navigation(["I,1", "S I", "R"], 2009)
        page = "Paulys Realencyclopädie der classischen Altertumswissenschaft/Statistik"
        compare(
            True,
            text.startswith(
                '{| class="wikitable" style="width:100%; border-color:#4b77d6"\n'
                '! style="background:#4b77d6; color:#fff; border-color:#4b77d6" | Jahre\n'
                "|-\n"
                '| style="background:#e4ebf9; border-color:#4b77d6" | '
                f"[[{page}/2007|2007]] · [[{page}/2008|2008]] · [[{page}/2009|2009]]\n"
                "|-\n"
                '! style="background:#4b77d6; color:#fff; border-color:#4b77d6" | Bände\n'
                "|-\n"
                '| style="background:#e4ebf9; border-color:#4b77d6" | '
                f"[[{page}/I,1|I,1]] · [[{page}/S I|S I]] · [[{page}/R|R]]\n"
                "|}<noinclude>"
            ),
        )

    def test_page_text_embeds_navigation(self):
        text = HistoryCharts.create_page_text("TABLE", "DETAIL_TABLE", 2026)
        compare(True, '| style="width:50%; vertical-align:top" | {{RE Statistik Navigation}}\n' in text)
