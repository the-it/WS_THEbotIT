import sys
import unittest

loader = unittest.TestLoader()
start_dir = '.'
SUITE = loader.discover(start_dir, pattern='*_test.py')

runner = unittest.TextTestRunner()

ret = not runner.run(SUITE).wasSuccessful()
sys.exit(ret)
