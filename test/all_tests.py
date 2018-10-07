from pathlib import Path
import sys
import unittest

LOADER = unittest.TestLoader()
SUITE = LOADER.discover(start_dir=Path(__file__).parent.parent)
RUNNER = unittest.TextTestRunner()
sys.exit(not RUNNER.run(SUITE).wasSuccessful())
