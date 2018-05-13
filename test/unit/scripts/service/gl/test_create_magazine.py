from datetime import datetime, timedelta
import time
import json
import os

import pywikibot

from scripts.service.gl.create_magazine import search_for_refs
from tools.bots import WikiLogger
from tools.catscan import PetScan
from scripts.service.ws_re.data_types import RePage, ReDatenException
from test import *
from test.unit.tools.test_bots import setup_data_path, teardown_data_path


@ddt
class TestSearchForRefs(TestCase):
    @file_data("scan_for_refs.json")
    def test_data_provider(self, value):
        for item in value:
            self.assertEqual(item[1], search_for_refs(item[0]),
                             "\"{}\" should convert to \"{}\"".format(item[0], item[1]))
