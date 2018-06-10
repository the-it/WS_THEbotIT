from test import TestCase


class ToolException(Exception):
    pass


__all__ = ['ToolException', 'catscan', 'template_handler', 'abbyy_xml', 'bots', 'date_conversion',
           'make_html_color']


def make_html_color(min_value, max_value, value):
    if max_value >= min_value:
        color = (1 - (value - min_value) / (max_value - min_value)) * 255
    else:
        color = ((value - max_value) / (min_value - max_value)) * 255
    color = max(0, min(255, color))
    return str(hex(round(color)))[2:].zfill(2).upper()


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
