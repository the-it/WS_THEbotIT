import importlib
from unittest import TestCase


class TestRunner(TestCase):
    def test_module_imports(self):
        # the runner only wires the scheduler together below its __main__ guard, importing it is the
        # cheapest way to notice a broken import path before the scheduled run does
        runner = importlib.import_module("service.runner")
        self.assertTrue(hasattr(runner, "BotScheduler"))
