import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from pywikibot import Page
from pywikibot.site import BaseSite

from service.ws_re.register.statistic.base import (
    lemmas_per_column,
    load_volume_lemmas,
    render_template,
    save_json_page,
    save_page,
)
from service.ws_re.volumes import Volume
from tools.bots.logger import WikiLogger

STATISTIC_PAGE = "Paulys Realencyclopädie der classischen Altertumswissenschaft/Statistik"
START_YEAR = 2007
# proof read state counted in each column of the data. The columns are ordered by the fields of the template
# history_data.json. The chart renderer stacks the series of an area chart in column order, the first series at the
# bottom. It colors the series in column order with a fixed palette (blue, yellow, red, teal, ...), there is no
# option to choose the colors. The order of the fields therefore determines the colors.
STATE_OF_COLUMN: dict[str, int] = {"erfasst": 0, "korrigiert": 2, "unkorrigiert": 1, "fertig": 3}


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

    @staticmethod
    def _parse_datestamp(datestamp: str) -> date:
        """Converts a datestamp of the history (format yymmdd) to a date."""
        return date(2000 + int(datestamp[0:2]), int(datestamp[2:4]), int(datestamp[4:6]))

    @staticmethod
    def _state_at(history: list[tuple[date, int]], day: date) -> int | None:
        """
        The history of a lemma records the date each state was entered. The state at a given day is the state of the
        latest entry up to that day.

        :param history: entries of the history as (date, state) sorted chronologically
        :return: the state at the day, None if the article didn't exist at that day
        """
        state = None
        for entry_date, entry_state in history:
            if entry_date > day:
                break
            state = entry_state
        return state

    @staticmethod
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

    def build_rows(self, volumes: VolumeLemmas, today: date, columns: list[str]) -> list[list[str | int]]:
        """
        Sums up the weights of the lemmas per proof read state at every end of a quarter. A lemma without an entry in
        its history up to that day isn't counted. The sums are rounded to integers.

        :param columns: names of the count columns, see STATE_OF_COLUMN
        :return: one row per day: the day (YYYY-MM-DD) followed by the sums in the order of the columns
        """
        histories = []
        for lemma, weight in self.weights(volumes):
            history = lemma.get("history") or {}
            entries = sorted((self._parse_datestamp(datestamp), int(state)) for state, datestamp in history.items())
            histories.append((entries, weight))
        rows: list[list[str | int]] = []
        for day in self._quarter_ends(today):
            sums: dict[int, float] = dict.fromkeys(STATE_OF_COLUMN.values(), 0.0)
            for entries, weight in histories:
                if (state := self._state_at(entries, day)) is not None:
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
            )
        )


ARTICLE_CHART = HistoryChart(
    name="Pauly-Wissowa/stats/main",
    unit_de="Artikel",
    unit_en="articles",
    counted_de="Artikel",
    counted_en="articles",
    weights=_article_weights,
)
COLUMN_CHART = HistoryChart(
    name="Pauly-Wissowa/stats/pages",
    unit_de="Spalten",
    unit_en="columns",
    counted_de="Spalten der Artikel",
    counted_en="columns of the articles",
    weights=_column_weights,
)


class HistoryCharts:
    """Maintains the history charts on Commons and the statistic page on wikisource, that embeds them."""

    CHARTS = (ARTICLE_CHART, COLUMN_CHART)

    def __init__(self, wiki: BaseSite, commons: BaseSite, logger: WikiLogger):
        self.wiki = wiki
        self.commons = commons
        self.logger = logger

    def update(self, today: date) -> None:
        self.logger.info("Update the history charts.")
        volumes = list(load_volume_lemmas())
        for chart in self.CHARTS:
            save_json_page(Page(self.commons, f"Data:{chart.name}.tab"), chart.create_data(volumes, today), self.logger)
            save_json_page(Page(self.commons, f"Data:{chart.name}.chart"), chart.create_definition(), self.logger)
        save_page(Page(self.wiki, STATISTIC_PAGE), self.create_page_text(), self.logger)

    @staticmethod
    def create_page_text() -> str:
        return render_template("statistic_page.wiki", article_chart=ARTICLE_CHART.name, column_chart=COLUMN_CHART.name)
