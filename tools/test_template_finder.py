from unittest.case import TestCase

from tools.template_finder import TemplateFinder, TemplateFinderException, TemplatePosition


class TestTemplateFinder(TestCase):
    def test_find_simple_template(self):
        finder = TemplateFinder("{{Template}}")
        self.assertListEqual([TemplatePosition(0, 12, "{{Template}}")], finder.get_positions("Template"))

    def test_find_simple_template_fail(self):
        finder = TemplateFinder("{{Template")
        with self.assertRaises(TemplateFinderException):
            finder.get_positions("Template")

    def test_find_two_templates(self):
        finder = TemplateFinder("{{Template}}{{Template}}")
        self.assertListEqual([TemplatePosition(0, 12, "{{Template}}"),
                              TemplatePosition(12, 24, "{{Template}}")], finder.get_positions("Template"))

    def test_find_template_with_argument(self):
        finder = TemplateFinder("{{OtherTemplate}}{{Template|test}}")
        self.assertListEqual([TemplatePosition(17, 34, "{{Template|test}}")], finder.get_positions("Template"))

    def test_find_nested_template(self):
        finder = TemplateFinder("{{Template|{{OtherTemplate}}}}")
        self.assertListEqual([TemplatePosition(0, 30, "{{Template|{{OtherTemplate}}}}")],
                             finder.get_positions("Template"))

    def test_find_nested_template_with_offset(self):
        finder = TemplateFinder("1234567890{{Template|{{OtherTemplate}}}}")
        self.assertListEqual([TemplatePosition(10, 40, "{{Template|{{OtherTemplate}}}}")],
                             finder.get_positions("Template"))

    def test_find_complex(self):
        finder = TemplateFinder("{{Template|{{{}}{{}}}}")
        self.assertListEqual([TemplatePosition(0, 22, "{{Template|{{{}}{{}}}}")],
                             finder.get_positions("Template"))

    def test_get_start_positions_of_regex(self):
        finder = TemplateFinder("{{a{{b{{")
        self.assertListEqual([0, 3, 6], finder.get_start_positions_of_regex("{{", "{{a{{b{{"))
