import json
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import date, timedelta

from pywikibot import Page
from pywikibot.site import BaseSite

from service.ws_re.register.statistic.base import (
    AREA_OPACITY,
    CHART_PALETTE,
    history_entries,
    lemmas_per_column,
    load_volume_lemmas,
    mix_with_white,
    render_template,
    save_json_page,
    save_page,
    state_at,
)
from service.ws_re.register.statistic.picture import ProofReadPicture
from service.ws_re.volumes import Volume
from tools.bots.logger import WikiLogger

STATISTIC_PAGE = "Paulys Realencyclopädie der classischen Altertumswissenschaft/Statistik"
START_YEAR = 2007
# proof read state counted in each column of the data. The columns are ordered by the fields of the template
# history_data.json. The chart renderer stacks the series of an area chart in column order, the first series at the
# bottom. It colors the series in column order with a fixed palette (blue, yellow, red, teal, ...), there is no
# option to choose the colors. The order of the fields therefore determines the colors.
STATE_OF_COLUMN: dict[str, int] = {"erfasst": 0, "korrigiert": 2, "unkorrigiert": 1, "fertig": 3}
# order of the columns of the table, it differs from the order of the series in the charts
TABLE_COLUMNS = ("erfasst", "unkorrigiert", "korrigiert", "fertig")


def _area_color(color: str) -> str:
    """The color of an area in the chart: the color of the series at AREA_OPACITY on a white background."""
    return "#" + "".join(f"{channel:02x}" for channel in mix_with_white(color, AREA_OPACITY))


VolumeLemmas = list[tuple[Volume, list[dict]]]
WeightedLemmas = list[tuple[dict, float]]


def _article_weights(volumes: VolumeLemmas) -> WeightedLemmas:
    """Every article counts once."""
    return [(lemma, 1.0) for _, lemmas in volumes for lemma in lemmas]


def _column_weights(volumes: VolumeLemmas) -> WeightedLemmas:
    """
    Every article counts with its parts of the columns, the lemmas are distributed over the columns like in the
    proof read picture. A column shared by n articles contributes 1/n to each of them, so a column is completely
    fertig only if all of its articles are fertig. Volumes without known columns are skipped.
    """
    weighted: WeightedLemmas = []
    for volume, lemmas in volumes:
        if volume.start_column is None or volume.end_column is None:
            continue
        weights = [0.0] * len(lemmas)
        length = volume.end_column - volume.start_column + 1
        for indices in lemmas_per_column(lemmas, volume.start_column, length):
            for index in indices:
                weights[index] += 1 / len(indices)
        weighted.extend((lemma, weight) for lemma, weight in zip(lemmas, weights, strict=True) if weight)
    return weighted


def _quarter_ends(today: date) -> list[date]:
    """All ends of a quarter from the first quarter of START_YEAR up to today, plus today itself."""
    days = []
    for year in range(START_YEAR, today.year + 1):
        for month, day in ((3, 31), (6, 30), (9, 30), (12, 31)):
            quarter_end = date(year, month, day)
            if quarter_end >= today:
                days.append(today)
                return days
            days.append(quarter_end)
    return days  # pragma: no cover


def _sundays(today: date) -> list[date]:
    """
    All sundays of the current year up to today. Before the first sunday of the year it is today only, a chart needs
    at least one data point.
    """
    first_day = date(today.year, 1, 1)
    # Monday is 0, Sunday is 6
    sunday = first_day + timedelta(days=(6 - first_day.weekday()) % 7)
    days = []
    while sunday <= today:
        days.append(sunday)
        sunday += timedelta(days=7)
    return days or [today]


@dataclass(frozen=True)
class Period:
    """The days of a chart and how they are described."""

    days: Callable[[date], list[date]]
    # appended to the title of the chart
    title_suffix_de: str
    title_suffix_en: str
    # end of the description of the data
    interval_de: str
    interval_en: str


QUARTERLY = Period(
    days=_quarter_ends,
    title_suffix_de="",
    title_suffix_en="",
    interval_de="jeweils zum Ende eines Quartals",
    interval_en="at the end of every quarter",
)
WEEKLY = Period(
    days=_sundays,
    title_suffix_de=" im laufenden Jahr",
    title_suffix_en=" in the current year",
    interval_de="jeweils sonntags im laufenden Jahr",
    interval_en="every Sunday of the current year",
)


@dataclass(frozen=True)
class HistoryChart:
    """
    Area chart of the articles per proof read state over time, each article weighted by the weights function. The
    data (.tab) and the definition (.chart) of the chart live on Commons, both are rendered from the same templates
    for every chart.
    """

    name: str
    # what the chart counts, e.g. "Artikel" / "articles"
    unit_de: str
    unit_en: str
    # what the description of the data counts, e.g. "Spalten der Artikel" / "columns of the articles"
    counted_de: str
    counted_en: str
    weights: Callable[[VolumeLemmas], WeightedLemmas]
    period: Period

    def build_rows(self, volumes: VolumeLemmas, today: date, columns: list[str]) -> list[list[str | int]]:
        """
        Sums up the weights of the lemmas per proof read state at every day of the period. A lemma without an entry in
        its history up to that day isn't counted. The sums are rounded to integers.

        :param columns: names of the count columns, see STATE_OF_COLUMN
        :return: one row per day: the day (YYYY-MM-DD) followed by the sums in the order of the columns
        """
        histories = [(history_entries(lemma), weight) for lemma, weight in self.weights(volumes)]
        rows: list[list[str | int]] = []
        for day in self.period.days(today):
            sums: dict[int, float] = dict.fromkeys(STATE_OF_COLUMN.values(), 0.0)
            for entries, weight in histories:
                if (state := state_at(entries, day)) is not None:
                    sums[state] += weight
            rows.append([day.isoformat(), *(round(sums[STATE_OF_COLUMN[column]]) for column in columns)])
        return rows

    def create_data(self, volumes: VolumeLemmas, today: date) -> dict:
        """Content of the tabular data page (Data:….tab) on Commons."""
        data = json.loads(
            render_template(
                "history_data.json",
                statistic_page=STATISTIC_PAGE,
                counted_de=self.counted_de,
                counted_en=self.counted_en,
                interval_de=self.period.interval_de,
                interval_en=self.period.interval_en,
            )
        )
        # the first field is the date
        columns = [field["name"] for field in data["schema"]["fields"][1:]]
        data["data"] = self.build_rows(volumes, today, columns)
        return data

    def create_definition(self) -> dict:
        """Content of the chart definition page (Data:….chart) on Commons."""
        return json.loads(
            render_template(
                "history_chart.json",
                name=self.name,
                unit_de=self.unit_de,
                unit_en=self.unit_en,
                axis_en=self.unit_en.capitalize(),
                title_suffix_de=self.period.title_suffix_de,
                title_suffix_en=self.period.title_suffix_en,
            )
        )

    def with_period(self, name: str, period: Period) -> HistoryChart:
        return replace(self, name=name, period=period)


ARTICLE_CHART = HistoryChart(
    name="Pauly-Wissowa/stats/articles",
    unit_de="Artikel",
    unit_en="articles",
    counted_de="Artikel",
    counted_en="articles",
    weights=_article_weights,
    period=QUARTERLY,
)
COLUMN_CHART = HistoryChart(
    name="Pauly-Wissowa/stats/columns",
    unit_de="Spalten",
    unit_en="columns",
    counted_de="Spalten der Artikel",
    counted_en="columns of the articles",
    weights=_column_weights,
    period=QUARTERLY,
)
ARTICLE_DETAIL_CHART = ARTICLE_CHART.with_period(f"{ARTICLE_CHART.name} detail", WEEKLY)
COLUMN_DETAIL_CHART = COLUMN_CHART.with_period(f"{COLUMN_CHART.name} detail", WEEKLY)


class HistoryCharts:
    """Maintains the history charts on Commons and the statistic page on wikisource, that embeds them."""

    # every group of charts gets a joined table of its data
    GROUPS = ((ARTICLE_CHART, COLUMN_CHART), (ARTICLE_DETAIL_CHART, COLUMN_DETAIL_CHART))

    def __init__(self, wiki: BaseSite, commons: BaseSite, logger: WikiLogger):
        self.wiki = wiki
        self.commons = commons
        self.logger = logger

    def update(self, today: date) -> None:
        self.logger.info("Update the history charts.")
        volumes = list(load_volume_lemmas())
        tables: list[str] = []
        for group in self.GROUPS:
            datasets: list[tuple[HistoryChart, dict]] = []
            for chart in group:
                data = chart.create_data(volumes, today)
                save_json_page(Page(self.commons, f"Data:{chart.name}.tab"), data, self.logger)
                save_json_page(Page(self.commons, f"Data:{chart.name}.chart"), chart.create_definition(), self.logger)
                datasets.append((chart, data))
            tables.append(self.create_table(datasets))
        save_page(Page(self.wiki, STATISTIC_PAGE), self.create_page_text(*tables), self.logger)

    @staticmethod
    def create_table(datasets: list[tuple[HistoryChart, dict]]) -> str:
        """
        One wiki table of the content of all tabular data pages, newest row first. All data pages share the same days.
        Every chart gets a group of columns (ordered by TABLE_COLUMNS), headed by its unit. The header of a series has
        the color of the series in the chart, its data cells the color of its area.
        """
        groups = "\n".join(f'! colspan="{len(TABLE_COLUMNS)}" | {chart.unit_de}' for chart, _ in datasets)
        # per dataset the index of every table column in the data rows, the first field of the data is the date
        indices = [
            [[field["name"] for field in data["schema"]["fields"]].index(column) for column in TABLE_COLUMNS]
            for _, data in datasets
        ]
        headers = [
            f'style="background:{CHART_PALETTE[index - 1]}" | {data["schema"]["fields"][index]["title"]["de"]}'
            for (_, data), group in zip(datasets, indices, strict=True)
            for index in group
        ]
        columns = "! " + " !! ".join(headers)
        rows = []
        for day_rows in reversed(list(zip(*(data["data"] for _, data in datasets), strict=True))):
            cells = [str(day_rows[0][0])]
            for day_row, group in zip(day_rows, indices, strict=True):
                cells.extend(
                    f'style="background:{_area_color(CHART_PALETTE[index - 1])}" | {{{{formatnum:{day_row[index]}}}}}'
                    for index in group
                )
            rows.append("|-\n| " + " || ".join(cells))
        return render_template("history_table.wiki", groups=groups, columns=columns, rows="\n".join(rows)).rstrip("\n")

    @staticmethod
    def create_page_text(table: str, detail_table: str) -> str:
        return render_template(
            "statistic_page.wiki",
            article_chart=ARTICLE_CHART.name,
            column_chart=COLUMN_CHART.name,
            picture=ProofReadPicture.WIKI_FILE_NAME,
            table=table,
            article_detail_chart=ARTICLE_DETAIL_CHART.name,
            column_detail_chart=COLUMN_DETAIL_CHART.name,
            detail_table=detail_table,
        )
