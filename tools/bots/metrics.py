import os
from collections.abc import Callable
from datetime import datetime
from typing import Self

from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.metrics import Observation
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource

_EXPORT_TIMEOUT_SECONDS = 5


class BotMetrics:
    def __init__(
        self,
        bot_name: str,
        start_time: datetime,
        endpoint: str | None = None,
        enabled: bool | None = None,
        log_error: Callable[[str], None] | None = None,
    ):
        self._bot_name: str = bot_name
        self._start_time: datetime = start_time
        # Passed through as-is to OTLPMetricExporter(endpoint=...) only when explicitly set here;
        # left None otherwise so the exporter resolves OTEL_EXPORTER_OTLP_ENDPOINT itself.
        self._endpoint: str | None = endpoint
        self.enabled: bool = (
            enabled if enabled is not None else bool(endpoint or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"))
        )
        self._log_error: Callable[[str], None] = log_error or (lambda msg: None)
        # (kind, name, attributes) -> value ; kind is "counter" or "gauge"
        self._data: dict[tuple[str, str, frozenset], float] = {}

    def increment(self, name: str, value: float = 1, **attributes: str) -> None:
        key = ("counter", name, frozenset(attributes.items()))
        self._data[key] = self._data.get(key, 0) + value

    def gauge(self, name: str, value: float, **attributes: str) -> None:
        key = ("gauge", name, frozenset(attributes.items()))
        self._data[key] = value

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.flush()

    def flush(self) -> None:
        if not self.enabled or not self._data:
            return
        try:
            self._export()
        except Exception as exception:  # noqa: BLE001 pylint: disable=broad-except
            self._log_error(f"Could not send metrics for bot {self._bot_name}: {exception}")

    def _export(self) -> None:
        exporter = OTLPMetricExporter(endpoint=self._endpoint, timeout=_EXPORT_TIMEOUT_SECONDS)
        reader = PeriodicExportingMetricReader(exporter, export_interval_millis=_EXPORT_TIMEOUT_SECONDS * 1000)
        provider = MeterProvider(resource=Resource.create({"service.name": "ws_thebotit"}), metric_readers=[reader])
        meter = provider.get_meter(self._bot_name)

        counter_points: dict[str, list[tuple[dict, float]]] = {}
        gauge_points: dict[str, list[tuple[dict, float]]] = {}
        for (kind, name, attrs), value in self._data.items():
            attributes = dict(attrs)
            attributes["bot"] = self._bot_name
            (counter_points if kind == "counter" else gauge_points).setdefault(name, []).append((attributes, value))

        for name, points in counter_points.items():
            counter = meter.create_counter(name)
            for attributes, value in points:
                counter.add(value, attributes)

        for name, points in gauge_points.items():
            meter.create_observable_gauge(name, callbacks=[self._gauge_callback(points)])

        provider.shutdown()

    @staticmethod
    def _gauge_callback(points: list[tuple[dict, float]]):
        def callback(_options):
            return [Observation(value, attributes) for attributes, value in points]

        return callback
