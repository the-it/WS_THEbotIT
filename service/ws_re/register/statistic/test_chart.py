# pylint: disable=protected-access
from datetime import date
from unittest import mock

from testfixtures import compare

from service.ws_re.register.statistic.chart import (
    ARTICLE_CHART,
    COLUMN_CHART,
    HistoryChart,
    HistoryCharts,
    _article_weights,
    _column_weights,
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
    def test_parse_datestamp(self):
        compare(date(2013, 3, 5), HistoryChart._parse_datestamp("130305"))

    def test_state_at(self):
        history = [(date(2010, 1, 1), 0), (date(2012, 6, 1), 2), (date(2015, 1, 1), 3)]
        compare(None, HistoryChart._state_at(history, date(2009, 12, 31)))
        compare(0, HistoryChart._state_at(history, date(2010, 1, 1)))
        compare(2, HistoryChart._state_at(history, date(2014, 12, 31)))
        compare(3, HistoryChart._state_at(history, date(2020, 1, 1)))
        compare(None, HistoryChart._state_at([], date(2020, 1, 1)))

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
            HistoryChart._quarter_ends(date(2008, 5, 1)),
        )

    def test_quarter_ends_today_is_quarter_end(self):
        compare([date(2007, 3, 31), date(2007, 6, 30)], HistoryChart._quarter_ends(date(2007, 6, 30)))

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
        compare("Pauly-Wissowa/stats/main.tab", definition["source"])
        compare("Paulys Realencyclopädie: Artikel nach Bearbeitungsstand", definition["title"]["de"])
        compare("Paulys Realencyclopädie: articles by proofreading status", definition["title"]["en"])
        compare({"title": {"de": "Artikel", "en": "Articles"}}, definition["yAxis"])

    def test_create_definition_columns(self):
        definition = COLUMN_CHART.create_definition()
        compare("Pauly-Wissowa/stats/pages.tab", definition["source"])
        compare("Paulys Realencyclopädie: Spalten nach Bearbeitungsstand", definition["title"]["de"])
        compare({"title": {"de": "Spalten", "en": "Columns"}}, definition["yAxis"])


class TestHistoryCharts(BaseTestRegister):
    def test_create_page_text(self):
        text = HistoryCharts.create_page_text()
        compare(True, "{{#chart:Pauly-Wissowa/stats/main.chart}}" in text)
        compare(True, "{{#chart:Pauly-Wissowa/stats/pages.chart}}" in text)
        compare(True, text.index("=== Artikel ===") < text.index("=== Spalten ==="))

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
                mock.call(commons, "Data:Pauly-Wissowa/stats/main.tab"),
                mock.call(commons, "Data:Pauly-Wissowa/stats/main.chart"),
                mock.call(commons, "Data:Pauly-Wissowa/stats/pages.tab"),
                mock.call(commons, "Data:Pauly-Wissowa/stats/pages.chart"),
                mock.call(wiki, "Paulys Realencyclopädie der classischen Altertumswissenschaft/Statistik"),
            ],
            page_mock.call_args_list,
        )
        compare(4, save_json_mock.call_count)
        compare("2007-02-01", save_json_mock.call_args_list[0].args[1]["data"][0][0])
        compare(ARTICLE_CHART.create_definition(), save_json_mock.call_args_list[1].args[1])
        compare(COLUMN_CHART.create_definition(), save_json_mock.call_args_list[3].args[1])
        compare(HistoryCharts.create_page_text(), save_mock.call_args.args[1])
