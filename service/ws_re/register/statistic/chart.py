import json
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import date, timedelta

from pywikibot import Page
from pywikibot.site import BaseSite

from service.ws_re.register.statistic.base import (
    AREA_OPACITY,
    CHART_PALETTE,
    PAST_YEARS,
    STATISTIC_VOLUMES,
    Color,
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
NAVIGATION_TEMPLATE = "RE Statistik Navigation"
# the cells of the navigation get the blue of the charts at this opacity, light enough for readable links
NAVIGATION_CELL_OPACITY = 0.15
START_YEAR = 2007
# proof read state counted in each column of the data. The columns are ordered by the fields of the template
# history_data.json. The chart renderer stacks the series of an area chart in column order, the first series at the
# bottom. It colors the series in column order with a fixed palette (blue, yellow, red, teal, ...), there is no
# option to choose the colors. The order of the fields therefore determines the colors.
STATE_OF_COLUMN: dict[str, int] = {"erfasst": 0, "korrigiert": 2, "unkorrigiert": 1, "fertig": 3}
# order of the columns of the table, it differs from the order of the series in the charts
TABLE_COLUMNS = ("erfasst", "unkorrigiert", "korrigiert", "fertig")


def _hex(color: Color) -> str:
    return "#" + "".join(f"{channel:02x}" for channel in color)


def _area_color(color: str) -> str:
    """The color of an area in the chart: the color of the series at AREA_OPACITY on a white background."""
    return _hex(mix_with_white(color, AREA_OPACITY))


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
    # the chart definition is shared by the statistic pages of all years
    title_suffix_de=" im Jahr",
    title_suffix_en=" in the year",
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
    # every year and every volume has its own tabular data page (name of the chart plus the year or the volume), all
    # of them share the chart definition
    suffix: str | None = None

    @property
    def tab_name(self) -> str:
        return f"{self.name} {self.suffix}" if self.suffix else self.name

    @property
    def embedding(self) -> str:
        """Arguments of the #chart parser function, that embeds the chart with its data."""
        return f"{self.name}.chart|data={self.tab_name}.tab"

    def _with_weekly_year(self, year: int) -> Period:
        if self.period is WEEKLY:
            return replace(
                self.period, interval_de=f"jeweils sonntags im Jahr {year}", interval_en=f"every Sunday of {year}"
            )
        return self.period

    def of_year(self, year: int) -> HistoryChart:
        return replace(self, suffix=str(year), period=self._with_weekly_year(year))

    def of_volume(self, volume_name: str, year: int) -> HistoryChart:
        """The chart of the articles of a single volume, the weekly data covers the year."""
        return replace(
            self,
            suffix=volume_name,
            period=self._with_weekly_year(year),
            counted_de=f"{self.counted_de} des Bandes {volume_name}",
            counted_en=f"{self.counted_en} of volume {volume_name}",
        )

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
        """Content of the chart definition page (Data:….chart) on Commons, its default data is the one of the year."""
        return json.loads(
            render_template(
                "history_chart.json",
                source=self.tab_name,
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


def chart_groups(year: int, volume_name: str | None = None) -> tuple[tuple[HistoryChart, ...], ...]:
    """
    The groups of charts of the statistic page of a year or of a volume, every group gets a joined table of its data.
    All pages share the chart definitions, every year and every volume has its own data pages, named with the year or
    the volume. The weekly charts of a volume cover the given (current) year.
    """
    charts = (ARTICLE_CHART, COLUMN_CHART), (ARTICLE_DETAIL_CHART, COLUMN_DETAIL_CHART)
    return tuple(
        tuple(chart.of_volume(volume_name, year) if volume_name else chart.of_year(year) for chart in group)
        for group in charts
    )


class HistoryCharts:
    """Maintains the history charts on Commons and the statistic pages on wikisource, that embed them."""

    def __init__(self, wiki: BaseSite, commons: BaseSite, logger: WikiLogger):
        self.wiki = wiki
        self.commons = commons
        self.logger = logger

    def update(self, today: date) -> None:
        self.logger.info("Update the history charts.")
        volumes = list(load_volume_lemmas())
        save_page(
            Page(self.wiki, f"Vorlage:{NAVIGATION_TEMPLATE}"),
            self.create_navigation([volume.name for volume, _ in volumes], today.year),
            self.logger,
        )
        # every year gets its own page, a past year shows the state at its end
        for year in PAST_YEARS:
            if year < today.year:
                self.update_year(volumes, year, date(year, 12, 31), today.year)
        self.update_year(volumes, today.year, today, today.year)
        # the statistic page redirects to the page of the current year
        save_page(Page(self.wiki, STATISTIC_PAGE), f"#WEITERLEITUNG [[{STATISTIC_PAGE}/{today.year}]]", self.logger)
        # some volumes get their own page with the state of today
        for volume_name in STATISTIC_VOLUMES:
            self.update_volume([item for item in volumes if item[0].name == volume_name], volume_name, today)

    def update_year(self, volumes: VolumeLemmas, year: int, day: date, current_year: int) -> None:
        """Updates the charts of the year on Commons and the statistic page of the year, the data ends with the day."""
        # the shared definitions link the data of the current year
        tables = self._update_data(volumes, chart_groups(year), day, save_definitions=year == current_year)
        save_page(
            Page(self.wiki, f"{STATISTIC_PAGE}/{year}"),
            self.create_page_text(tables[0], tables[1], year),
            self.logger,
        )

    def update_volume(self, volumes: VolumeLemmas, volume_name: str, today: date) -> None:
        """Updates the charts of the volume on Commons and the statistic page of the volume."""
        tables = self._update_data(volumes, chart_groups(today.year, volume_name), today, save_definitions=False)
        save_page(
            Page(self.wiki, f"{STATISTIC_PAGE}/{volume_name}"),
            self.create_page_text(tables[0], tables[1], today.year, volume_name),
            self.logger,
        )

    def _update_data(
        self, volumes: VolumeLemmas, groups: tuple[tuple[HistoryChart, ...], ...], day: date, save_definitions: bool
    ) -> list[str]:
        """Saves the data pages of the charts up to the day, returns a joined table of the data of every group."""
        tables: list[str] = []
        for group in groups:
            datasets: list[tuple[HistoryChart, dict]] = []
            for chart in group:
                data = chart.create_data(volumes, day)
                save_json_page(Page(self.commons, f"Data:{chart.tab_name}.tab"), data, self.logger)
                if save_definitions:
                    save_json_page(
                        Page(self.commons, f"Data:{chart.name}.chart"), chart.create_definition(), self.logger
                    )
                datasets.append((chart, data))
            tables.append(self.create_table(datasets))
        return tables

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
    def create_navigation(volume_names: list[str], year: int) -> str:
        """Navigation template linking the statistic pages of every year since START_YEAR and of every volume."""
        years = " · ".join(f"[[{STATISTIC_PAGE}/{page_year}|{page_year}]]" for page_year in range(START_YEAR, year + 1))
        volumes = " · ".join(f"[[{STATISTIC_PAGE}/{name}|{name}]]" for name in volume_names)
        # the blue of the charts (Erfasst) for the headers and a very light tone of it for the cells
        return render_template(
            "navigation.wiki",
            header=CHART_PALETTE[0],
            cell=_hex(mix_with_white(CHART_PALETTE[0], NAVIGATION_CELL_OPACITY)),
            years=years,
            volumes=volumes,
        )

    @staticmethod
    def create_page_text(table: str, detail_table: str, year: int, volume_name: str | None = None) -> str:
        """Text of the statistic page of the year, or of the volume (its weekly charts cover the year)."""
        (article_chart, column_chart), (article_detail_chart, column_detail_chart) = chart_groups(year, volume_name)
        picture = ProofReadPicture.volume_file_name(volume_name) if volume_name else ProofReadPicture.file_name(year)
        return render_template(
            "statistic_page.wiki",
            article_chart=article_chart.embedding,
            column_chart=column_chart.embedding,
            navigation=NAVIGATION_TEMPLATE,
            picture=picture,
            table=table,
            year=str(year),
            article_detail_chart=article_detail_chart.embedding,
            column_detail_chart=column_detail_chart.embedding,
            detail_table=detail_table,
        )
