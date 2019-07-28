import sys
import unittest

LOADER = unittest.TestLoader()
SUITE = LOADER.discover(start_dir=".")
RUNNER = unittest.TextTestRunner()
sys.exit(not RUNNER.run(SUITE).wasSuccessful())
