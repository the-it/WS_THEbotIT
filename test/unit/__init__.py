from test import *


class TestIsSubTuple(TestCase):
    def test_int(self):
        self.assertTrue(is_subtuple((1, 2), (0, 1, 2, 3)))
        self.assertFalse(is_subtuple((1, 2), (0, 1, 3, 2)))
        self.assertFalse(is_subtuple((0, 2), (1, 3, 2)))
        self.assertFalse(is_subtuple((1, 4), (0, 1, 3, 2)))

    def test_complex_string_tuples(self):
        self.assertTrue(is_subtuple((("1", "2"), ("3", "4")), (("0", "0"), ("1", "2"), ("3", "4"), ("5", "6"))))
        self.assertFalse(is_subtuple((("1", "2"), ("3", "4")), (("0", "0"), ("1", "2"), ("0", "0"), ("3", "4"), ("5", "6"))))