from test import *

from tools import make_html_color


class TestMakeHtmlColor(TestCase):
    def test_in_range(self):
        self.assertEqual("80", make_html_color(10, 20, 15))
        self.assertEqual("80", make_html_color(11, 19, 15))
        self.assertEqual("40", make_html_color(10, 20, 17.5))

    def test_max_and_min(self):
        self.assertEqual("00", make_html_color(10, 20, 20))
        self.assertEqual("FF", make_html_color(10, 20, 10))

    def test_out_of_limits(self):
        self.assertEqual("00", make_html_color(10, 20, 21))
        self.assertEqual("FF", make_html_color(10, 20, 9))

    def test_recursive(self):
        self.assertEqual("40", make_html_color(20, 10, 12.5))
        self.assertEqual("FF", make_html_color(20, 10, 20))
        self.assertEqual("00", make_html_color(20, 10, 10))
