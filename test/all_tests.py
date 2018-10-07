from pathlib import Path
import sys
import unittest

from tools import path_to_str

LOADER = unittest.TestLoader()
SUITE = LOADER.discover(start_dir=path_to_str(Path(__file__).parent.parent))
RUNNER = unittest.TextTestRunner()
sys.exit(not RUNNER.run(SUITE).wasSuccessful())
