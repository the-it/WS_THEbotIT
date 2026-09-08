"""Manual smoke-test bot to verify metrics actually reach a local OTel collector.

Not part of the automated test suite. Run it directly, pointed at a running collector:

    OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 uv run python -m tools.bots.manual_metrics_bot

Then inspect what the collector received: metric names, the "bot" attribute, temporality.
Requires the usual AWS credentials (WS_AWS_PRD_KEY/WS_AWS_PRD_SECRET or WS_AWS_TST_ENV) since
CloudBot's StatusManager/PersistedData need them, same as any other bot.
"""

import time

from tools.bots.cloud_bot import CloudBot


class ManualMetricsBot(CloudBot):
    def task(self) -> bool:
        self.metrics.increment("manual_metrics_bot_smoke_total")
        self.metrics.gauge("manual_metrics_bot_smoke_value", 42)
        with self.time_step("example_step"):
            time.sleep(0.1)
        time.sleep(3)
        return True


if __name__ == "__main__":
    with ManualMetricsBot(log_to_screen=True, log_to_wiki=False, send_metrics=True) as bot:
        bot.run()
