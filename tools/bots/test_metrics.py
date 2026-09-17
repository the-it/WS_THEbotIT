# pylint: disable=protected-access,no-member,no-self-use
from datetime import datetime
from unittest import TestCase, mock

from tools.bots.metrics import BotMetrics

START_TIME = datetime(year=2000, month=1, day=1)


class TestBotMetrics(TestCase):
    def test_disabled_by_default_without_endpoint(self):
        metrics = BotMetrics("test_bot", START_TIME)
        self.assertFalse(metrics.enabled)

    def test_enabled_when_endpoint_given(self):
        metrics = BotMetrics("test_bot", START_TIME, endpoint="http://localhost:4317")
        self.assertTrue(metrics.enabled)

    def test_enabled_flag_overrides_endpoint(self):
        metrics = BotMetrics("test_bot", START_TIME, endpoint="http://localhost:4317", enabled=False)
        self.assertFalse(metrics.enabled)
        metrics = BotMetrics("test_bot", START_TIME, enabled=True)
        self.assertTrue(metrics.enabled)

    def test_increment_accumulates(self):
        metrics = BotMetrics("test_bot", START_TIME, enabled=True)
        metrics.increment("bot_run_total")
        metrics.increment("bot_run_total")
        metrics.increment("bot_run_total", value=3)
        self.assertEqual(5, metrics._data[("counter", "bot_run_total", frozenset())])

    def test_increment_keeps_attributes_separate(self):
        metrics = BotMetrics("test_bot", START_TIME, enabled=True)
        metrics.increment("bot_run_total", success="True")
        metrics.increment("bot_run_total", success="False")
        self.assertEqual(1, metrics._data[("counter", "bot_run_total", frozenset({("success", "True")}))])
        self.assertEqual(1, metrics._data[("counter", "bot_run_total", frozenset({("success", "False")}))])

    def test_gauge_overwrites(self):
        metrics = BotMetrics("test_bot", START_TIME, enabled=True)
        metrics.gauge("bot_run_duration_seconds", 1.0)
        metrics.gauge("bot_run_duration_seconds", 2.0)
        self.assertEqual(2.0, metrics._data[("gauge", "bot_run_duration_seconds", frozenset())])

    def test_flush_is_noop_when_disabled(self):
        metrics = BotMetrics("test_bot", START_TIME, enabled=False)
        metrics.increment("bot_run_total")
        with mock.patch.object(BotMetrics, "_export") as mock_export:
            metrics.flush()
        mock_export.assert_not_called()

    def test_flush_is_noop_when_no_data(self):
        metrics = BotMetrics("test_bot", START_TIME, enabled=True)
        with mock.patch.object(BotMetrics, "_export") as mock_export:
            metrics.flush()
        mock_export.assert_not_called()

    def test_flush_exports_when_enabled_and_has_data(self):
        metrics = BotMetrics("test_bot", START_TIME, enabled=True)
        metrics.increment("bot_run_total")
        with mock.patch.object(BotMetrics, "_export") as mock_export:
            metrics.flush()
        mock_export.assert_called_once()

    def test_flush_logs_and_swallows_export_errors(self):
        log_error = mock.Mock()
        metrics = BotMetrics("test_bot", START_TIME, enabled=True, log_error=log_error)
        metrics.increment("bot_run_total")
        with mock.patch.object(BotMetrics, "_export", side_effect=Exception("boom")):
            metrics.flush()  # must not raise
        log_error.assert_called_once()
        self.assertIn("test_bot", log_error.call_args[0][0])

    def test_context_manager_flushes_on_exit(self):
        metrics = BotMetrics("test_bot", START_TIME, enabled=True)
        metrics.increment("bot_run_total")
        with mock.patch.object(BotMetrics, "_export") as mock_export, metrics:
            pass
        mock_export.assert_called_once()

    def test_export_sends_counters_and_gauges_with_bot_attribute(self):
        metrics = BotMetrics("test_bot", START_TIME, endpoint="http://localhost:4317", enabled=True)
        metrics.increment("bot_run_total", success="True")
        metrics.gauge("bot_run_duration_seconds", 1.5)

        counter_mock = mock.Mock()
        meter_mock = mock.Mock()
        meter_mock.create_counter.return_value = counter_mock
        provider_mock = mock.Mock()
        provider_mock.get_meter.return_value = meter_mock

        with (
            mock.patch("tools.bots.metrics.OTLPMetricExporter") as mock_exporter,
            mock.patch("tools.bots.metrics.PeriodicExportingMetricReader") as mock_reader,
            mock.patch("tools.bots.metrics.MeterProvider", return_value=provider_mock) as mock_provider,
        ):
            metrics._export()

        mock_exporter.assert_called_once_with(endpoint="http://localhost:4317", timeout=5)
        mock_reader.assert_called_once()
        mock_provider.assert_called_once()
        counter_mock.add.assert_called_once_with(1, {"success": "True", "bot": "test_bot"})
        meter_mock.create_observable_gauge.assert_called_once()
        gauge_name, gauge_kwargs = meter_mock.create_observable_gauge.call_args
        self.assertEqual("bot_run_duration_seconds", gauge_name[0])
        observations = gauge_kwargs["callbacks"][0](None)
        self.assertEqual(1, len(observations))
        self.assertEqual(1.5, observations[0].value)
        self.assertEqual({"bot": "test_bot"}, observations[0].attributes)
        provider_mock.shutdown.assert_called_once()
